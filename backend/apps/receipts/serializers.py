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

    class Meta:
        model = Receipt
        fields = [
            "id", "image", "store_location", "store_number", "purchase_date",
            "receipt_number", "invoice_number", "parse_status", "parse_error",
            "created_at", "line_items",
        ]
        read_only_fields = ["parse_status", "parse_error", "created_at"]


class ReceiptUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Receipt
        fields = ["id", "image"]


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
                LineItem(receipt=instance, position=i, **item)
                for i, item in enumerate(items)
            ])
        return instance
