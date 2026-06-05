"""Pricing service layer — matching, observation recording, drop detection.

All logic is generic and provider-agnostic: it calls the configured
`PriceProvider` (NullProvider by default, so everything is a no-op until a real
provider is injected).
"""

from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from apps.receipts.models import LineItem

from . import get_price_provider
from .base import PriceResult
from .models import PriceAlert, PriceObservation, Product


def match_line_item_to_product(line_item: LineItem) -> Product | None:
    """Link a confirmed product line item to a tracked Product.

    Primary key is the item number; fall back to a provider name search.
    Sets `line_item.product` + `tracking_status`.
    """
    if line_item.item_type != LineItem.ItemType.PRODUCT:
        return None  # service / discount stay SKIPPED

    if line_item.item_number:
        product, _ = Product.objects.get_or_create(
            item_number=line_item.item_number,
            defaults={"name": line_item.raw_name},
        )
    else:
        candidates = get_price_provider().search(line_item.raw_name)
        if not candidates:
            line_item.tracking_status = LineItem.TrackingStatus.UNTRACKED
            line_item.save(update_fields=["tracking_status"])
            return None
        best = candidates[0]
        product, _ = Product.objects.get_or_create(
            item_number=best.item_number,
            defaults={"name": best.name or line_item.raw_name, "url": best.url or ""},
        )

    line_item.product = product
    line_item.tracking_status = LineItem.TrackingStatus.MATCHED
    line_item.save(update_fields=["product", "tracking_status"])
    return product


def record_observation(product: Product, result: PriceResult) -> PriceObservation:
    """Persist a price reading and refresh the product's current price."""
    obs = PriceObservation.objects.create(
        product=product,
        price=result.current_price,
        on_sale=result.on_sale,
        source=result.source,
    )
    product.current_price = result.current_price
    product.on_sale = result.on_sale
    product.last_checked = timezone.now()
    if result.name and not product.name:
        product.name = result.name
    if result.url and not product.url:
        product.url = result.url
    product.save(
        update_fields=["current_price", "on_sale", "last_checked", "name", "url", "updated_at"]
    )
    return obs


def evaluate_price_drop(product: Product) -> list[PriceAlert]:
    """Open/refresh an alert for each tracked purchase now cheaper than paid."""
    if product.current_price is None:
        return []
    window_days = getattr(settings, "PRICE_CHECK_ADJUSTMENT_DAYS", 30)
    today = timezone.localdate()
    alerts: list[PriceAlert] = []

    line_items = LineItem.objects.filter(
        product=product,
        tracking_status=LineItem.TrackingStatus.MATCHED,
        receipt__parse_status="confirmed",
    ).select_related("receipt")

    for li in line_items:
        if li.unit_price is None or li.unit_price <= product.current_price:
            continue
        purchase_date = li.receipt.purchase_date
        within = bool(
            purchase_date and purchase_date >= today - timedelta(days=window_days)
        )
        alert, _ = PriceAlert.objects.update_or_create(
            user_id=li.receipt.user_id,
            line_item=li,
            defaults={
                "observed_price": product.current_price,
                "purchase_price": li.unit_price,
                "delta": li.unit_price - product.current_price,
                "within_adjustment_window": within,
            },
        )
        alerts.append(alert)
    return alerts
