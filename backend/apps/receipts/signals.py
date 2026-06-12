"""Receipt file lifecycle.

A Receipt row owns exactly one uploaded file. Deleting the row (user action,
account cascade, or retention purge) must not leave the file orphaned on disk —
Django's FileField does NOT remove the file on delete, so we do it here. Using
post_delete means a single hook covers every delete path.
"""

import logging
import os

from django.conf import settings
from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import Receipt

logger = logging.getLogger(__name__)


@receiver(post_delete, sender=Receipt)
def delete_receipt_file(sender, instance: Receipt, **kwargs) -> None:
    image = instance.image
    if not image:
        return
    name = image.name
    try:
        # Check existence before deleting so a missing file is a no-op, not an error.
        if image.storage.exists(name):
            image.delete(save=False)
            logger.info("deleted receipt file %s", name)
    except Exception:  # never let cleanup failure break the delete transaction
        logger.exception("failed to delete receipt file %s", name)
        return
    _prune_empty_dirs(image.storage, name)


def _prune_empty_dirs(storage, name: str) -> None:
    """Remove the now-empty parent dirs the deleted file left behind, walking up
    to (but never removing) MEDIA_ROOT — so per-user `home/<uuid>/...` trees don't
    accumulate as empty shells (esp. after retention purges). Filesystem storage
    only; a no-op for storages without real directories (e.g. object stores)."""
    try:
        media_root = os.path.realpath(str(settings.MEDIA_ROOT))
        d = os.path.realpath(os.path.dirname(storage.path(name)))
    except Exception:  # non-filesystem storage (no .path()) or unresolved root
        return
    while d != media_root and d.startswith(media_root + os.sep):
        try:
            os.rmdir(d)  # succeeds only if empty
        except OSError:
            break  # non-empty (or already gone) → stop climbing
        d = os.path.dirname(d)
