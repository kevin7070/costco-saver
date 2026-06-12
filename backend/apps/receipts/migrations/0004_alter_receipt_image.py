import apps.receipts.models
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("receipts", "0003_lineitem_product"),
    ]

    operations = [
        migrations.AlterField(
            model_name="receipt",
            name="image",
            field=models.FileField(upload_to=apps.receipts.models.receipt_upload_path),
        ),
    ]
