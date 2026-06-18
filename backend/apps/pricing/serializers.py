"""Pricing serializers — read-only alert + product summary."""

from rest_framework import serializers

from .models import PriceAlert, Product


class ProductSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "item_number", "name", "url", "current_price", "on_sale"]


class PriceAlertSerializer(serializers.ModelSerializer):
    product = ProductSummarySerializer(source="line_item.product", read_only=True)
    # Raw name from the receipt (may differ from Product.name if the catalog entry is richer)
    item_name = serializers.CharField(source="line_item.raw_name", read_only=True)
    store_location = serializers.CharField(
        source="line_item.receipt.store_location", read_only=True
    )
    purchase_date = serializers.DateField(
        source="line_item.receipt.purchase_date", read_only=True
    )

    class Meta:
        model = PriceAlert
        fields = [
            "id", "status",
            "observed_price", "purchase_price", "delta",
            "within_adjustment_window",
            "created_at", "updated_at",
            "product", "item_name", "store_location", "purchase_date",
        ]
        read_only_fields = [
            "id", "observed_price", "purchase_price", "delta",
            "within_adjustment_window", "created_at", "updated_at",
        ]
