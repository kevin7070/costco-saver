"""Auth endpoint tests."""

import pytest
from django.urls import reverse

from .factories import UserFactory


@pytest.mark.django_db
class TestLogin:
    def test_success_sets_cookies(self, api_client):
        user = UserFactory(email="alice@example.com", password="testpass123")
        url = reverse("auth:login")
        resp = api_client.post(
            url,
            {"email": "alice@example.com", "password": "testpass123"},
            format="json",
        )
        assert resp.status_code == 200
        assert "access_token" in resp.cookies
        assert "refresh_token" in resp.cookies
        assert resp.data["user"]["email"] == "alice@example.com"

    def test_wrong_password_returns_400(self, api_client):
        UserFactory(email="alice@example.com", password="testpass123")
        resp = api_client.post(
            reverse("auth:login"),
            {"email": "alice@example.com", "password": "wrong"},
            format="json",
        )
        assert resp.status_code == 400

    def test_unknown_email_returns_400(self, api_client):
        resp = api_client.post(
            reverse("auth:login"),
            {"email": "nobody@example.com", "password": "x"},
            format="json",
        )
        assert resp.status_code == 400


@pytest.mark.django_db
class TestMe:
    def test_authenticated_returns_user(self, user_client, user):
        resp = user_client.get(reverse("auth:me"))
        assert resp.status_code == 200
        assert resp.data["email"] == user.email

    def test_unauthenticated_returns_401(self, api_client):
        resp = api_client.get(reverse("auth:me"))
        assert resp.status_code == 401


@pytest.mark.django_db
class TestChangePassword:
    def test_success(self, user_client, user):
        user.set_password("oldpass123")
        user.save()
        user_client.force_authenticate(user=user)
        resp = user_client.post(
            reverse("auth:change-password"),
            {"current_password": "oldpass123", "new_password": "newpass456"},
            format="json",
        )
        assert resp.status_code == 200
        user.refresh_from_db()
        assert user.check_password("newpass456")

    def test_wrong_current_password_returns_400(self, user_client, user):
        user.set_password("oldpass123")
        user.save()
        user_client.force_authenticate(user=user)
        resp = user_client.post(
            reverse("auth:change-password"),
            {"current_password": "wrong", "new_password": "newpass456"},
            format="json",
        )
        assert resp.status_code == 400
