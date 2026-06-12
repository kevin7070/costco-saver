"""Receipt file lifecycle.

A Receipt row owns exactly one uploaded file. Deleting the row (user action,
account cascade, or retention purge) must not leave the file orphaned on disk —
Django's FileField does NOT remove the file on delete, so we do it here. Using
post_delete means a single hook covers every delete path.
"""

import logging

from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import Receipt

logger = logging.getLogger(__name__)


@receiver(post_delete, sender=Receipt)
def delete_receipt_file(sender, instance: Receipt, **kwargs) -> None:
    image = instance.image
    if not image:
        return
    try:
        # Check existence before deleting so a missing file is a no-op, not an error.
        if image.storage.exists(image.name):
            image.delete(save=False)
            logger.info("deleted receipt file %s", image.name)
    except Exception:  # never let cleanup failure break the delete transaction
        logger.exception("failed to delete receipt file %s", getattr(image, "name", "?"))
