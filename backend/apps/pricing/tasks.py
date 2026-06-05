"""Celery tasks: refresh tracked product prices + fan-out scheduler.

`refresh_prices` is routed to the `price_refresh` queue. With the default
NullProvider, `lookup()` returns None and the whole chain is a no-op.
"""

from __future__ import annotations

import logging
from datetime import timedelta

from celery import shared_task
from django.db.models import Q
from django.utils import timezone

from . import get_price_provider
from .models import Product
from .services import evaluate_price_drop, record_observation

logger = logging.getLogger(__name__)


@shared_task(
    name="apps.pricing.tasks.refresh_prices",
    bind=True,
    acks_late=True,
    max_retries=2,
    default_retry_delay=60,
)
def refresh_prices(self, product_id: str) -> None:
    try:
        product = Product.objects.get(pk=product_id)
    except Product.DoesNotExist:
        logger.warning("refresh_prices: product %s no longer exists", product_id)
        return

    try:
        result = get_price_provider().lookup(product.item_number)
    except Exception as exc:  # noqa: BLE001 — provider is a remote dependency
        logger.exception("refresh_prices: provider failed for %s", product_id)
        raise self.retry(exc=exc)

    if result is None or result.current_price is None:
        product.last_checked = timezone.now()
        product.save(update_fields=["last_checked"])
        return

    record_observation(product, result)
    evaluate_price_drop(product)


@shared_task(name="apps.pricing.tasks.enqueue_due_checks")
def enqueue_due_checks(max_age_hours: int = 24) -> int:
    """Fan out refresh_prices for products whose price reading is stale."""
    cutoff = timezone.now() - timedelta(hours=max_age_hours)
    due = Product.objects.filter(
        Q(last_checked__isnull=True) | Q(last_checked__lt=cutoff)
    )
    count = 0
    for product_id in due.values_list("id", flat=True):
        refresh_prices.delay(str(product_id))
        count += 1
    logger.info("enqueue_due_checks: queued %d product(s)", count)
    return count
