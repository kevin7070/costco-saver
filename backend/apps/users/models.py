"""User model — email-based auth with a simple user_type flag (admin / user)."""

from django.contrib.auth.models import AbstractUser
from django.db import models
from uuid6 import uuid7

from .managers import UserManager


class UserType(models.TextChoices):
    ADMIN = "admin", "Admin"
    USER = "user", "User"


class User(AbstractUser):
    """Custom User with email-based auth."""

    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    username = None
    email = models.EmailField("email address", unique=True)

    user_type = models.CharField(
        max_length=20,
        choices=UserType.choices,
        default=UserType.USER,
    )
    # Email ownership confirmed via the verification link.
    email_verified = models.BooleanField(default=False)

    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    timezone = models.CharField(max_length=50, default="UTC")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = UserManager()

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        self.email = self.email.lower().strip()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email

    @property
    def is_admin(self) -> bool:
        return self.user_type == UserType.ADMIN

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip() or self.email
