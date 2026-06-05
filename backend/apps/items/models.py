"""Sample Item model — demonstrates the domain-app pattern.

Replace with your actual domain entities. Keep the shape (status field,
service-mediated transitions, audit timestamps, owner FK) as a template.
"""

from django.conf import settings
from django.db import models
from uuid6 import uuid7


class ItemStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    ARCHIVED = "archived", "Archived"


class Item(models.Model):
    """A sample item owned by a user.

    Status lifecycle: active → archived (via archive_item service).
    """

    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=ItemStatus.choices,
        default=ItemStatus.ACTIVE,
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="items",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["owner", "status"]),
        ]

    def __str__(self):
        return self.name

    @property
    def is_active(self) -> bool:
        return self.status == ItemStatus.ACTIVE
