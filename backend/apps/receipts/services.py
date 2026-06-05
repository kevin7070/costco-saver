"""Receipt service layer — upload, apply parse result, (review handled in serializer)."""

from __future__ import annotations

from datetime import date

from django.db import transaction
from django.utils import timezone

from apps.parsers.base import StructuredReceipt

from .models import LineItem, Receipt


def create_receipt(*, user, image) -> Receipt:
    """Store an uploaded receipt and queue it for parsing."""
    receipt = Receipt.objects.create(
        user=user, image=image, enqueued_at=timezone.now()
    )
    # Local import avoids an app-load import cycle (tasks imports models).
    from .tasks import parse_receipt

    parse_receipt.delay(str(receipt.id))
    return receipt


@transaction.atomic
def apply_parse_result(receipt: Receipt, parsed: StructuredReceipt) -> Receipt:
    """Write a StructuredReceipt onto the Receipt + LineItems; status → needs_review."""
    receipt.store_location = parsed.store_location or ""
    receipt.store_number = parsed.store_number or ""
    receipt.purchase_date = _parse_date(parsed.purchase_date)
    receipt.receipt_number = parsed.receipt_number or ""
    receipt.invoice_number = parsed.invoice_number or ""
    receipt.raw_parse = parsed.raw
    receipt.parse_status = Receipt.ParseStatus.NEEDS_REVIEW
    receipt.parse_error = ""
    receipt.save()

    receipt.line_items.all().delete()
    LineItem.objects.bulk_create([
        LineItem(
            receipt=receipt,
            raw_name=li.raw_name,
            item_number=li.item_number or "",
            quantity=li.quantity,
            unit_price=li.unit_price,
            amount=li.amount,
            item_type=li.item_type,
            taxable=li.taxable,
            tracking_status=LineItem.initial_tracking_status(li.item_type),
            position=i,
        )
        for i, li in enumerate(parsed.line_items)
    ])
    return receipt


def _parse_date(s: str | None) -> date | None:
    if not s:
        return None
    try:
        y, m, d = (int(x) for x in s.split("-"))
        return date(y, m, d)
    except (ValueError, TypeError):
        return None
