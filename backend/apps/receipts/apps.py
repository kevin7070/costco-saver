from django.apps import AppConfig


class ReceiptsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.receipts"

    def ready(self) -> None:
        from . import signals  # noqa: F401  (register post_delete file cleanup)
