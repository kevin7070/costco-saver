"""Celery tasks for receipt parsing.

`parse_receipt` is routed to the single-concurrency `receipt_parse` queue
(settings.CELERY_TASK_ROUTES) so the vision LLM is never hit concurrently.
"""

import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from apps.parsers import get_parser

from .models import Receipt
from .services import apply_parse_result

logger = logging.getLogger(__name__)


@shared_task(
    name="apps.receipts.tasks.parse_receipt",
    bind=True,
    acks_late=True,
    max_retries=2,
    default_retry_delay=30,
)
def parse_receipt(self, receipt_id: str) -> None:
    try:
        receipt = Receipt.objects.get(pk=receipt_id)
    except Receipt.DoesNotExist:
        logger.warning("parse_receipt: receipt %s no longer exists", receipt_id)
        return

    receipt.parse_status = Receipt.ParseStatus.PROCESSING
    receipt.save(update_fields=["parse_status"])

    try:
        with receipt.image.open("rb") as fh:
            data = fh.read()
        content_type = (
            "application/pdf"
            if receipt.image.name.lower().endswith(".pdf")
            else "image/jpeg"
        )
        parsed = get_parser().parse(data, content_type=content_type)
        apply_parse_result(receipt, parsed)
    except Exception as exc:  # noqa: BLE001 — record + retry
        logger.exception("parse_receipt failed for receipt %s", receipt_id)
        receipt.parse_status = Receipt.ParseStatus.FAILED
        receipt.parse_error = str(exc)[:500]
        receipt.save(update_fields=["parse_status", "parse_error"])
        raise self.retry(exc=exc)


@shared_task(name="apps.receipts.tasks.purge_expired_receipts")
def purge_expired_receipts() -> int:
    """Retention: delete receipts older than RECEIPT_RETENTION_DAYS.

    `.delete()` cascades the line items and fires post_delete per receipt, so the
    stored files are cleaned up too (apps.receipts.signals). Runs daily via beat.
    """
    cutoff = timezone.now() - timedelta(days=settings.RECEIPT_RETENTION_DAYS)
    expired = Receipt.objects.filter(created_at__lt=cutoff)
    count = expired.count()
    if count:
        expired.delete()
        logger.info(
            "purged %d receipt(s) older than %d days",
            count, settings.RECEIPT_RETENTION_DAYS,
        )
    return count
