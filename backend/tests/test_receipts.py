"""Tests for the receipts app (parser + Celery enqueue mocked)."""

from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from apps.parsers.base import StructuredLineItem, StructuredReceipt
from apps.receipts.models import LineItem, Receipt
from apps.receipts.services import apply_parse_result
from apps.receipts.tasks import catalog_match_receipt, purge_expired_receipts

pytestmark = pytest.mark.django_db


def _structured():
    return StructuredReceipt(
        store_location="Markham #151",
        store_number="151",
        purchase_date="2026-06-04",
        receipt_number="22015120500102606040916",
        invoice_number="205663",
        line_items=[
            StructuredLineItem("X-LIGHT OIL", "142372", 1, Decimal("28.99"), Decimal("28.99"), "product", False),
            StructuredLineItem("INSTANT SAVINGS", "207SE40", 1, Decimal("-6.0"), Decimal("-6.0"), "discount", False),
            StructuredLineItem("NEOFLAM 12PC", "8523320Z", 1, Decimal("29.99"), Decimal("29.99"), "product", True),
        ],
        raw={"ok": True},
    )


def test_apply_parse_result(user):
    r = Receipt.objects.create(user=user, image="receipts/x.jpg")
    apply_parse_result(r, _structured())
    r.refresh_from_db()
    assert r.parse_status == Receipt.ParseStatus.NEEDS_REVIEW
    assert r.store_number == "151"
    assert str(r.purchase_date) == "2026-06-04"
    assert r.receipt_number == "22015120500102606040916"
    items = list(r.line_items.all())
    assert len(items) == 3
    assert items[1].item_type == "discount"
    assert items[1].tracking_status == LineItem.TrackingStatus.SKIPPED  # discount not tracked
    assert items[0].tracking_status == LineItem.TrackingStatus.PENDING  # product pending match
    assert items[2].taxable is True


def test_upload_creates_receipt_and_enqueues(user_client):
    img = SimpleUploadedFile("r.jpg", b"\xff\xd8jpeg-bytes", content_type="image/jpeg")
    with patch("apps.receipts.tasks.parse_receipt.delay") as delay:
        resp = user_client.post("/api/v1/receipts/", {"image": img}, format="multipart")
    assert resp.status_code == 201
    assert delay.called
    assert Receipt.objects.count() == 1


def test_list_only_own_receipts(user_client, user, admin_user):
    Receipt.objects.create(user=user, image="a.jpg")
    Receipt.objects.create(user=admin_user, image="b.jpg")
    resp = user_client.get("/api/v1/receipts/")
    assert resp.status_code == 200
    data = resp.json()
    results = data["results"] if isinstance(data, dict) else data
    assert len(results) == 1


def test_confirm_corrects_and_sets_confirmed(user_client, user):
    r = Receipt.objects.create(
        user=user, image="a.jpg", parse_status=Receipt.ParseStatus.NEEDS_REVIEW
    )
    LineItem.objects.create(receipt=r, raw_name="WRONG OCR", position=0)
    payload = {
        "store_location": "Markham #151",
        "purchase_date": "2026-06-04",
        "receipt_number": "2201512",
        "invoice_number": "205663",
        "line_items": [
            {"raw_name": "X-LIGHT OIL", "item_number": "1422972", "quantity": 1,
             "unit_price": "28.99", "amount": "28.99", "item_type": "product", "taxable": False},
        ],
    }
    resp = user_client.post(f"/api/v1/receipts/{r.id}/confirm/", payload, format="json")
    assert resp.status_code == 200
    r.refresh_from_db()
    assert r.parse_status == Receipt.ParseStatus.CONFIRMED
    assert r.store_location == "Markham #151"
    items = list(r.line_items.all())
    assert len(items) == 1
    assert items[0].item_number == "1422972"  # user corrected


def test_image_action_serves_own_receipt(user_client):
    img = SimpleUploadedFile(
        "r.jpg", b"\xff\xd8\xff\xe0\x00\x10JFIF", content_type="image/jpeg"
    )
    with patch("apps.receipts.tasks.parse_receipt.delay"):
        up = user_client.post("/api/v1/receipts/", {"image": img}, format="multipart")
    rid = up.json()["id"]
    resp = user_client.get(f"/api/v1/receipts/{rid}/image/")
    assert resp.status_code == 200


def test_image_action_blocks_cross_user(user_client, admin_user):
    # Receipt belongs to admin_user; the plain user must not reach its image.
    r = Receipt.objects.create(user=admin_user, image="receipts/secret.jpg")
    resp = user_client.get(f"/api/v1/receipts/{r.id}/image/")
    assert resp.status_code == 404  # user-scoped queryset hides others' receipts


def test_image_action_requires_auth(api_client, user):
    r = Receipt.objects.create(user=user, image="receipts/x.jpg")
    resp = api_client.get(f"/api/v1/receipts/{r.id}/image/")
    assert resp.status_code == 401


def test_upload_rejects_svg_content_type(user_client):
    svg = SimpleUploadedFile(
        "x.svg",
        b"<svg><script>alert(1)</script></svg>",
        content_type="image/svg+xml",
    )
    resp = user_client.post("/api/v1/receipts/", {"image": svg}, format="multipart")
    assert resp.status_code == 400


def test_upload_rejects_disguised_svg(user_client):
    # SVG bytes but claims an allowed content-type — magic-byte check catches it.
    svg = SimpleUploadedFile(
        "x.png",
        b"<svg><script>alert(1)</script></svg>",
        content_type="image/png",
    )
    resp = user_client.post("/api/v1/receipts/", {"image": svg}, format="multipart")
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Deletion gate, file cleanup, retention, per-user storage path
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("status", ["confirmed", "failed"])
def test_destroy_allowed_when_deletable(user_client, user, status):
    r = Receipt.objects.create(user=user, image="x.jpg", parse_status=status)
    resp = user_client.delete(f"/api/v1/receipts/{r.id}/")
    assert resp.status_code == 204
    assert not Receipt.objects.filter(pk=r.pk).exists()


@pytest.mark.parametrize("status", ["queued", "processing", "needs_review"])
def test_destroy_blocked_until_confirmed(user_client, user, status):
    # In-flight (queued/processing) and unconfirmed (needs_review) can't be deleted.
    r = Receipt.objects.create(user=user, image="x.jpg", parse_status=status)
    resp = user_client.delete(f"/api/v1/receipts/{r.id}/")
    assert resp.status_code == 409
    assert Receipt.objects.filter(pk=r.pk).exists()


def test_destroy_cross_user_404(user_client, admin_user):
    r = Receipt.objects.create(user=admin_user, image="x.jpg", parse_status="confirmed")
    resp = user_client.delete(f"/api/v1/receipts/{r.id}/")
    assert resp.status_code == 404
    assert Receipt.objects.filter(pk=r.pk).exists()


def test_can_delete_flag_in_serializer(user_client, user):
    ok = Receipt.objects.create(user=user, image="a.jpg", parse_status="confirmed")
    no = Receipt.objects.create(user=user, image="b.jpg", parse_status="processing")
    assert user_client.get(f"/api/v1/receipts/{ok.id}/").data["can_delete"] is True
    assert user_client.get(f"/api/v1/receipts/{no.id}/").data["can_delete"] is False


def test_upload_path_is_per_user(user, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    r = Receipt.objects.create(
        user=user, image=SimpleUploadedFile("Scan.pdf", b"%PDF-1.4 x")
    )
    assert r.image.name.startswith(f"home/{user.id}/receipts/")
    assert r.image.name.endswith("Scan.pdf")


def test_destroy_removes_stored_file(user_client, user, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    r = Receipt.objects.create(
        user=user,
        image=SimpleUploadedFile("r.jpg", b"\xff\xd8jpeg", content_type="image/jpeg"),
        parse_status="confirmed",
    )
    name = r.image.name
    assert default_storage.exists(name)
    resp = user_client.delete(f"/api/v1/receipts/{r.id}/")
    assert resp.status_code == 204
    assert not default_storage.exists(name)  # post_delete signal cleaned it up


def test_purge_expired_receipts_drops_old_rows_and_files(user, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    old = Receipt.objects.create(
        user=user,
        image=SimpleUploadedFile("old.jpg", b"\xff\xd8old", content_type="image/jpeg"),
        parse_status="confirmed",
    )
    old_name = old.image.name
    # created_at is auto_now_add; backdate past the retention window via queryset.
    Receipt.objects.filter(pk=old.pk).update(
        created_at=timezone.now() - timedelta(days=400)
    )
    recent = Receipt.objects.create(
        user=user,
        image=SimpleUploadedFile("new.jpg", b"\xff\xd8new", content_type="image/jpeg"),
        parse_status="confirmed",
    )

    purged = purge_expired_receipts()

    assert purged == 1
    assert not Receipt.objects.filter(pk=old.pk).exists()
    assert not default_storage.exists(old_name)  # file cleaned via post_delete
    assert Receipt.objects.filter(pk=recent.pk).exists()  # still within retention


def test_delete_prunes_empty_parent_dirs(user_client, user, settings, tmp_path):
    import os

    settings.MEDIA_ROOT = str(tmp_path)
    r = Receipt.objects.create(
        user=user,
        image=SimpleUploadedFile("r.jpg", b"\xff\xd8x", content_type="image/jpeg"),
        parse_status="confirmed",
    )
    file_dir = os.path.dirname(os.path.join(str(tmp_path), r.image.name))
    user_home = os.path.join(str(tmp_path), "home", str(user.id))
    assert os.path.isdir(file_dir)

    assert user_client.delete(f"/api/v1/receipts/{r.id}/").status_code == 204

    # The file's dir and the now-empty per-user tree are pruned...
    assert not os.path.exists(file_dir)
    assert not os.path.exists(user_home)
    # ...but MEDIA_ROOT itself is kept.
    assert os.path.isdir(str(tmp_path))


def test_delete_keeps_dir_with_other_files(user_client, user, settings, tmp_path):
    # A user's month dir must survive while another receipt still lives in it.
    import os

    settings.MEDIA_ROOT = str(tmp_path)
    keep = Receipt.objects.create(
        user=user, image=SimpleUploadedFile("a.jpg", b"\xff\xd8a"), parse_status="confirmed"
    )
    drop = Receipt.objects.create(
        user=user, image=SimpleUploadedFile("b.jpg", b"\xff\xd8b"), parse_status="confirmed"
    )
    keep_dir = os.path.dirname(os.path.join(str(tmp_path), keep.image.name))

    assert user_client.delete(f"/api/v1/receipts/{drop.id}/").status_code == 204

    assert os.path.isdir(keep_dir)  # not pruned — still holds `keep`'s file
    assert default_storage.exists(keep.image.name)


# ---------------------------------------------------------------------------
# Catalog matching trigger (Gap #1)
# ---------------------------------------------------------------------------


def test_confirm_triggers_catalog_match(user_client, user):
    r = Receipt.objects.create(
        user=user, image="a.jpg", parse_status=Receipt.ParseStatus.NEEDS_REVIEW
    )
    payload = {
        "store_location": "Markham #151",
        "purchase_date": "2026-06-04",
        "receipt_number": "R001",
        "invoice_number": "I001",
        "line_items": [
            {
                "raw_name": "X-LIGHT OIL", "item_number": "142372",
                "quantity": 1, "unit_price": "28.99", "amount": "28.99",
                "item_type": "product", "taxable": False,
            },
        ],
    }
    with patch("apps.receipts.views.catalog_match_receipt") as mock_task:
        resp = user_client.post(f"/api/v1/receipts/{r.id}/confirm/", payload, format="json")
    assert resp.status_code == 200
    mock_task.delay.assert_called_once_with(str(r.id))


def test_catalog_match_receipt_matches_pending_items(user):
    r = Receipt.objects.create(
        user=user, image="a.jpg", parse_status=Receipt.ParseStatus.CONFIRMED
    )
    li = LineItem.objects.create(
        receipt=r, raw_name="X-LIGHT OIL", item_number="142372", position=0,
        tracking_status=LineItem.TrackingStatus.PENDING, item_type="product",
        quantity=1, unit_price=Decimal("28.99"), amount=Decimal("28.99"),
    )
    with patch("apps.pricing.tasks.refresh_prices") as mock_refresh:
        count = catalog_match_receipt(str(r.id))
    li.refresh_from_db()
    assert count == 1
    assert li.tracking_status == LineItem.TrackingStatus.MATCHED
    assert li.product is not None
    assert li.product.item_number == "142372"
    mock_refresh.delay.assert_called_once_with(str(li.product.pk))


def test_catalog_match_receipt_missing_receipt_is_noop():
    count = catalog_match_receipt("00000000-0000-0000-0000-000000000000")
    assert count == 0


def test_catalog_match_receipt_skips_non_pending_items(user):
    r = Receipt.objects.create(
        user=user, image="a.jpg", parse_status=Receipt.ParseStatus.CONFIRMED
    )
    # SKIPPED (discount) and already MATCHED items must not be re-processed.
    LineItem.objects.create(
        receipt=r, raw_name="INSTANT SAVINGS", position=0,
        tracking_status=LineItem.TrackingStatus.SKIPPED, item_type="discount",
    )
    LineItem.objects.create(
        receipt=r, raw_name="PREV PRODUCT", item_number="999", position=1,
        tracking_status=LineItem.TrackingStatus.MATCHED, item_type="product",
    )
    with patch("apps.pricing.tasks.refresh_prices") as mock_refresh:
        count = catalog_match_receipt(str(r.id))
    assert count == 0
    mock_refresh.delay.assert_not_called()
