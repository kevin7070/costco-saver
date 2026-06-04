import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Receipt",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("image", models.FileField(upload_to="receipts/%Y/%m/")),
                ("store_location", models.CharField(blank=True, max_length=200)),
                ("store_number", models.CharField(blank=True, max_length=20)),
                ("purchase_date", models.DateField(blank=True, null=True)),
                ("receipt_number", models.CharField(blank=True, db_index=True, max_length=64)),
                ("invoice_number", models.CharField(blank=True, max_length=32)),
                ("raw_parse", models.JSONField(blank=True, default=dict)),
                ("parse_status", models.CharField(choices=[("queued", "Queued"), ("processing", "Processing"), ("needs_review", "Needs review"), ("confirmed", "Confirmed"), ("failed", "Failed")], default="queued", max_length=16)),
                ("parse_error", models.TextField(blank=True)),
                ("enqueued_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="receipts", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="LineItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("raw_name", models.CharField(max_length=200)),
                ("item_number", models.CharField(blank=True, max_length=32)),
                ("quantity", models.PositiveIntegerField(default=1)),
                ("unit_price", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("amount", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("item_type", models.CharField(choices=[("product", "Product"), ("service", "Service"), ("discount", "Discount")], default="product", max_length=16)),
                ("taxable", models.BooleanField(default=False)),
                ("tracking_status", models.CharField(choices=[("pending", "Pending"), ("matched", "Matched"), ("untracked", "Untracked"), ("skipped", "Skipped")], default="pending", max_length=16)),
                ("position", models.PositiveIntegerField(default=0)),
                ("receipt", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="line_items", to="receipts.receipt")),
            ],
            options={"ordering": ["receipt", "position"]},
        ),
        migrations.AddConstraint(
            model_name="receipt",
            constraint=models.UniqueConstraint(condition=models.Q(("receipt_number__gt", "")), fields=("user", "receipt_number"), name="uniq_user_receipt_number"),
        ),
    ]
