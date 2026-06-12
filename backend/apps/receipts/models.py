"""Receipt + line item models.

The receipt is the source of truth (it records what was actually bought).
Parsing is OCR-imperfect, so a freshly parsed receipt lands in `needs_review`
and only becomes `confirmed` after the user checks it.
"""

from django.conf import settings
from django.db import models
from django.utils import timezone
from uuid6 import uuid7


def receipt_upload_path(instance: "Receipt", filename: str) -> str:
    """Per-user, per-month folder: home/<user_uuid>/receipts/<yyyy-mm>/<file>.

    Isolating each user's receipts under their own UUID keeps the media tree
    tidy and makes per-user cleanup straightforward. The month comes from upload
    time (created_at isn't assigned yet when the file is written).
    """
    return f"home/{instance.user_id}/receipts/{timezone.now():%Y-%m}/{filename}"


class Receipt(models.Model):
    class ParseStatus(models.TextChoices):
        QUEUED = "queued", "Queued"
        PROCESSING = "processing", "Processing"
        NEEDS_REVIEW = "needs_review", "Needs review"
        CONFIRMED = "confirmed", "Confirmed"
        FAILED = "failed", "Failed"

    # Statuses at which the user may delete the receipt: processing is finished
    # AND nothing is left in flight. `confirmed` = reviewed & accepted; `failed`
    # = parsing gave up (nothing to confirm, must not strand the user). The
    # in-flight states (`queued`/`processing`) and the not-yet-confirmed
    # `needs_review` are intentionally NOT user-deletable.
    USER_DELETABLE_STATUSES = frozenset({ParseStatus.CONFIRMED, ParseStatus.FAILED})

    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="receipts"
    )
    image = models.FileField(upload_to=receipt_upload_path)
    store_location = models.CharField(max_length=200, blank=True)
    store_number = models.CharField(max_length=20, blank=True)
    purchase_date = models.DateField(null=True, blank=True)
    # The long barcode number at the bottom of the receipt: dedup + return ref.
    receipt_number = models.CharField(max_length=64, blank=True, db_index=True)
    invoice_number = models.CharField(max_length=32, blank=True)
    raw_parse = models.JSONField(default=dict, blank=True)
    parse_status = models.CharField(
        max_length=16, choices=ParseStatus.choices, default=ParseStatus.QUEUED
    )
    parse_error = models.TextField(blank=True)
    enqueued_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            # Same barcode can't be uploaded twice by the same user.
            models.UniqueConstraint(
                fields=["user", "receipt_number"],
                condition=models.Q(receipt_number__gt=""),
                name="uniq_user_receipt_number",
            )
        ]

    def __str__(self) -> str:
        return f"Receipt {self.receipt_number or self.pk}"

    @property
    def user_can_delete(self) -> bool:
        """True once processing is done and the data is confirmed (or failed)."""
        return self.parse_status in self.USER_DELETABLE_STATUSES


class LineItem(models.Model):
    class ItemType(models.TextChoices):
        PRODUCT = "product", "Product"
        SERVICE = "service", "Service"
        DISCOUNT = "discount", "Discount"

    class TrackingStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        MATCHED = "matched", "Matched"
        UNTRACKED = "untracked", "Untracked"
        SKIPPED = "skipped", "Skipped"

    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    receipt = models.ForeignKey(
        Receipt, on_delete=models.CASCADE, related_name="line_items"
    )
    raw_name = models.CharField(max_length=200)
    item_number = models.CharField(max_length=32, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    item_type = models.CharField(
        max_length=16, choices=ItemType.choices, default=ItemType.PRODUCT
    )
    taxable = models.BooleanField(default=False)
    # Set by the matching step.
    product = models.ForeignKey(
        "pricing.Product",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="line_items",
    )
    tracking_status = models.CharField(
        max_length=16, choices=TrackingStatus.choices, default=TrackingStatus.PENDING
    )
    position = models.PositiveIntegerField(default=0)  # order on the receipt

    class Meta:
        ordering = ["receipt", "position"]

    def __str__(self) -> str:
        return f"{self.raw_name} ({self.item_type})"

    @staticmethod
    def initial_tracking_status(item_type: str) -> str:
        """Only products are price-tracked; service/discount skip tracking from the start."""
        if item_type in (LineItem.ItemType.SERVICE, LineItem.ItemType.DISCOUNT):
            return LineItem.TrackingStatus.SKIPPED
        return LineItem.TrackingStatus.PENDING
