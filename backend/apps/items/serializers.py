"""Item serializers."""

from rest_framework import serializers

from .models import Item


class ItemSerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source="owner.full_name", read_only=True)

    class Meta:
        model = Item
        fields = [
            "id",
            "name",
            "description",
            "status",
            "owner",
            "owner_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "status", "owner", "created_at", "updated_at"]
