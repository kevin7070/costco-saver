"""Item service functions — demonstrates service-first backend pattern.

Keep business transactions here. Views stay thin (permission +
validation + response). Any cross-model mutation or state-guarded
transition belongs in a service function.
"""

from django.db import transaction

from .models import Item, ItemStatus


def archive_item(item: Item) -> Item:
    """Archive an item. Only active items can be archived.

    Raises:
        ValueError: If the item is not in active status.
    """
    if item.status != ItemStatus.ACTIVE:
        raise ValueError(
            f"Cannot archive item in status {item.status}. "
            f"Only active items can be archived."
        )

    with transaction.atomic():
        item.status = ItemStatus.ARCHIVED
        item.save(update_fields=["status", "updated_at"])

    return item
