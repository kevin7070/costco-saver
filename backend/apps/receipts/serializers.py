from rest_framework import serializers

from .models import LineItem, Receipt


class LineItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = LineItem
        fields = [
            "id", "raw_name", "item_number", "quantity", "unit_price",
            "amount", "item_type", "taxable", "tracking_status", "position",
        ]


class ReceiptSerializer(serializers.ModelSerializer):
    line_items = LineItemSerializer(many=True, read_only=True)
    # Always relative (/media/...) regardless of serializer context, so the
    # frontend proxies it same-origin; build_absolute_uri would leak web:8000.
    image = serializers.SerializerMethodField()

    def get_image(self, obj):
        # Relative URL to the authorized image action; same-origin via the
        # frontend proxy (never expose the backend host).
        return f"/api/v1/receipts/{obj.pk}/image/" if obj.image else None

    class Meta:
        model = Receipt
        fields = [
            "id", "image", "store_location", "store_number", "purchase_date",
            "receipt_number", "invoice_number", "parse_status", "parse_error",
            "created_at", "line_items",
        ]
        read_only_fields = ["parse_status", "parse_error", "created_at"]


ALLOWED_UPLOAD_TYPES = {"image/jpeg", "image/png", "application/pdf"}
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB
# Magic-byte prefixes for the allowed types (JPEG SOI, PNG signature, PDF).
ALLOWED_MAGIC = (b"\xff\xd8", b"\x89PNG", b"%PDF")


class ReceiptUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Receipt
        fields = ["id", "image"]

    def validate_image(self, image):
        if image.size > MAX_UPLOAD_BYTES:
            raise serializers.ValidationError("File too large (max 10 MB).")
        if getattr(image, "content_type", "") not in ALLOWED_UPLOAD_TYPES:
            raise serializers.ValidationError(
                "Unsupported file type. Upload a JPEG, PNG, or PDF."
            )
        # Check magic bytes, not just the client content-type — an SVG/script
        # renamed with an image content-type would otherwise slip through and
        # become stored XSS (media is served same-origin).
        head = image.read(8)
        image.seek(0)
        if not any(head.startswith(m) for m in ALLOWED_MAGIC):
            raise serializers.ValidationError(
                "File contents do not match an image or PDF."
            )
        return image


class LineItemReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = LineItem
        fields = [
            "raw_name", "item_number", "quantity", "unit_price",
            "amount", "item_type", "taxable",
        ]


class ReceiptReviewSerializer(serializers.ModelSerializer):
    """User-corrected receipt; saving it flips status to confirmed."""

    line_items = LineItemReviewSerializer(many=True)

    class Meta:
        model = Receipt
        fields = [
            "store_location", "store_number", "purchase_date",
            "receipt_number", "invoice_number", "line_items",
        ]

    def update(self, instance, validated_data):
        items = validated_data.pop("line_items", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.parse_status = Receipt.ParseStatus.CONFIRMED
        instance.save()
        if items is not None:
            instance.line_items.all().delete()
            LineItem.objects.bulk_create([
                LineItem(
                    receipt=instance,
                    position=i,
                    tracking_status=LineItem.initial_tracking_status(
                        item.get("item_type", LineItem.ItemType.PRODUCT)
                    ),
                    **item,
                )
                for i, item in enumerate(items)
            ])
        return instance
