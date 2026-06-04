"""Celery tasks for receipt parsing.

`parse_receipt` is routed to the single-concurrency `receipt_parse` queue
(settings.CELERY_TASK_ROUTES) so the vision LLM is never hit concurrently.
"""

import logging

from celery import shared_task

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
def parse_receipt(self, receipt_id: int) -> None:
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
