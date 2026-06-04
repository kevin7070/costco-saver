"""Item API tests — demonstrates the CRUD + service test pattern."""

import pytest
from django.urls import reverse

from apps.items.models import Item, ItemStatus
from apps.items.services import archive_item

from .factories import ItemFactory, UserFactory


@pytest.mark.django_db
class TestItemService:
    def test_archive_active_item(self):
        item = ItemFactory(status=ItemStatus.ACTIVE)
        archive_item(item)
        item.refresh_from_db()
        assert item.status == ItemStatus.ARCHIVED

    def test_archive_already_archived_raises(self):
        item = ItemFactory(status=ItemStatus.ARCHIVED)
        with pytest.raises(ValueError, match="archived"):
            archive_item(item)


@pytest.mark.django_db
class TestItemAPI:
    def test_list_returns_own_items_only(self, user_client, user):
        ItemFactory.create_batch(3, owner=user)
        other_user = UserFactory()
        ItemFactory.create_batch(2, owner=other_user)

        resp = user_client.get("/api/v1/items/")
        assert resp.status_code == 200
        assert resp.data["count"] == 3

    def test_create_sets_owner_to_current_user(self, user_client, user):
        resp = user_client.post(
            "/api/v1/items/",
            {"name": "New item", "description": "hello"},
            format="json",
        )
        assert resp.status_code == 201
        assert Item.objects.filter(owner=user, name="New item").exists()

    def test_cannot_view_another_users_item(self, user_client):
        other_user = UserFactory()
        other_item = ItemFactory(owner=other_user)
        resp = user_client.get(f"/api/v1/items/{other_item.pk}/")
        assert resp.status_code == 404  # filtered out by queryset

    def test_unauthenticated_returns_401(self, api_client):
        resp = api_client.get("/api/v1/items/")
        assert resp.status_code == 401

    def test_archive_active_via_api(self, user_client, user):
        item = ItemFactory(owner=user, status=ItemStatus.ACTIVE)
        resp = user_client.post(f"/api/v1/items/{item.pk}/archive/")
        assert resp.status_code == 200
        item.refresh_from_db()
        assert item.status == ItemStatus.ARCHIVED

    def test_archive_already_archived_returns_400(self, user_client, user):
        item = ItemFactory(owner=user, status=ItemStatus.ARCHIVED)
        resp = user_client.post(f"/api/v1/items/{item.pk}/archive/")
        assert resp.status_code == 400
        assert "detail" in resp.data
