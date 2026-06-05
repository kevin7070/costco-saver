"""Pricing service + task tests.

Provider-agnostic: the default NullProvider keeps everything inert, and drop
detection is exercised by injecting a PriceResult directly (no live scraper).
"""

import datetime
from decimal import Decimal
from unittest.mock import patch

import pytest

from apps.pricing import get_price_provider
from apps.pricing.base import PriceResult
from apps.pricing.models import PriceObservation, Product
from apps.pricing.null_provider import NullProvider
from apps.pricing.services import (
    evaluate_price_drop,
    match_line_item_to_product,
    record_observation,
)
from apps.pricing.tasks import refresh_prices
from apps.receipts.models import LineItem, Receipt


@pytest.mark.django_db
class TestProvider:
    def test_factory_resolves_null_provider(self, settings):
        settings.PRICE_PROVIDER = "apps.pricing.null_provider.NullProvider"
        assert isinstance(get_price_provider(), NullProvider)

    def test_null_provider_is_inert(self):
        p = NullProvider()
        assert p.lookup("123") is None
        assert p.search("anything") == []


@pytest.mark.django_db
class TestMatching:
    def test_match_by_item_number(self, user):
        rcpt = Receipt.objects.create(user=user, parse_status="confirmed")
        li = LineItem.objects.create(
            receipt=rcpt,
            raw_name="Thing",
            item_number="999001",
            item_type=LineItem.ItemType.PRODUCT,
            unit_price=Decimal("10.00"),
        )
        product = match_line_item_to_product(li)
        li.refresh_from_db()
        assert product is not None
        assert product.item_number == "999001"
        assert li.product_id == product.id
        assert li.tracking_status == LineItem.TrackingStatus.MATCHED

    def test_non_product_is_skipped(self, user):
        rcpt = Receipt.objects.create(user=user, parse_status="confirmed")
        li = LineItem.objects.create(
            receipt=rcpt,
            raw_name="Member discount",
            item_type=LineItem.ItemType.DISCOUNT,
            unit_price=Decimal("-5.00"),
        )
        assert match_line_item_to_product(li) is None

    def test_no_item_number_no_candidates_untracked(self, user):
        # NullProvider.search() -> [] -> UNTRACKED
        rcpt = Receipt.objects.create(user=user, parse_status="confirmed")
        li = LineItem.objects.create(
            receipt=rcpt,
            raw_name="Mystery item",
            item_type=LineItem.ItemType.PRODUCT,
            unit_price=Decimal("10.00"),
        )
        assert match_line_item_to_product(li) is None
        li.refresh_from_db()
        assert li.tracking_status == LineItem.TrackingStatus.UNTRACKED


@pytest.mark.django_db
class TestObservationAndDrop:
    def _matched_line(self, user, paid, purchase_date):
        rcpt = Receipt.objects.create(
            user=user, parse_status="confirmed", purchase_date=purchase_date
        )
        li = LineItem.objects.create(
            receipt=rcpt,
            raw_name="Widget",
            item_number="999002",
            item_type=LineItem.ItemType.PRODUCT,
            unit_price=Decimal(paid),
        )
        product = match_line_item_to_product(li)
        return product, li

    def test_record_observation_updates_product(self, user):
        product, _ = self._matched_line(user, "20.00", datetime.date.today())
        obs = record_observation(
            product, PriceResult(item_number="999002", current_price=Decimal("15.00"), source="test")
        )
        product.refresh_from_db()
        assert obs.price == Decimal("15.00")
        assert product.current_price == Decimal("15.00")
        assert PriceObservation.objects.filter(product=product).count() == 1

    def test_drop_within_window_opens_alert(self, user):
        product, _ = self._matched_line(user, "20.00", datetime.date.today())
        record_observation(
            product, PriceResult(item_number="999002", current_price=Decimal("15.00"))
        )
        alerts = evaluate_price_drop(product)
        assert len(alerts) == 1
        assert alerts[0].delta == Decimal("5.00")
        assert alerts[0].within_adjustment_window is True

    def test_drop_outside_window_flagged(self, user):
        old = datetime.date.today() - datetime.timedelta(days=60)
        product, _ = self._matched_line(user, "20.00", old)
        record_observation(
            product, PriceResult(item_number="999002", current_price=Decimal("15.00"))
        )
        alerts = evaluate_price_drop(product)
        assert len(alerts) == 1
        assert alerts[0].within_adjustment_window is False

    def test_no_alert_when_not_cheaper(self, user):
        product, _ = self._matched_line(user, "20.00", datetime.date.today())
        record_observation(
            product, PriceResult(item_number="999002", current_price=Decimal("25.00"))
        )
        assert evaluate_price_drop(product) == []


@pytest.mark.django_db
class TestRefreshTask:
    def test_refresh_with_null_provider_is_noop(self, user):
        product = Product.objects.create(item_number="999003")
        refresh_prices.apply(args=[str(product.id)])
        product.refresh_from_db()
        # NullProvider returns None -> only last_checked is touched, no observation
        assert product.last_checked is not None
        assert PriceObservation.objects.filter(product=product).count() == 0

    def test_enqueue_due_checks_fans_out_stale_products(self, user):
        Product.objects.create(item_number="888001")  # last_checked None -> stale
        with patch("apps.pricing.tasks.refresh_prices.delay") as mock_delay:
            from apps.pricing.tasks import enqueue_due_checks

            count = enqueue_due_checks()
        assert count == 1
        mock_delay.assert_called_once()
