"""Pricing models — tracked products, price history, and price-drop alerts.

A Product is something we track the price of (keyed by its retailer item
number). PriceObservation is a timestamped price reading. PriceAlert flags a
tracked purchase whose current price dropped below what the user paid, with a
flag for whether it is still within the adjustment window.
"""

from __future__ import annotations

from django.conf import settings
from django.db import models
from uuid6 import uuid7


class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    item_number = models.CharField(max_length=32, unique=True, db_index=True)
    name = models.CharField(max_length=255, blank=True)
    url = models.URLField(blank=True)
    current_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    on_sale = models.BooleanField(default=False)
    last_checked = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["item_number"]

    def __str__(self) -> str:
        return f"{self.item_number} {self.name}".strip()


class PriceObservation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="observations"
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    on_sale = models.BooleanField(default=False)
    source = models.CharField(max_length=32, default="provider")
    observed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-observed_at"]
        indexes = [models.Index(fields=["product", "-observed_at"])]

    def __str__(self) -> str:
        return f"{self.product.item_number} @ {self.price}"


class PriceAlert(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        SEEN = "seen", "Seen"
        ACTIONED = "actioned", "Actioned"
        DISMISSED = "dismissed", "Dismissed"

    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="price_alerts"
    )
    line_item = models.ForeignKey(
        "receipts.LineItem", on_delete=models.CASCADE, related_name="price_alerts"
    )
    observed_price = models.DecimalField(max_digits=10, decimal_places=2)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    delta = models.DecimalField(max_digits=10, decimal_places=2)  # purchase - observed
    within_adjustment_window = models.BooleanField(default=False)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "line_item"], name="uniq_user_lineitem_alert"
            ),
        ]

    def __str__(self) -> str:
        return f"Alert {self.line_item_id}: save {self.delta}"
