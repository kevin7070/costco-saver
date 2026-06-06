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


@pytest.mark.django_db
class TestRegister:
    def test_success_creates_user_and_logs_in(self, api_client):
        resp = api_client.post(
            reverse("auth:register"),
            {
                "email": "new@example.com",
                "password": "S3curePass!9",
                "first_name": "New",
                "last_name": "User",
            },
            format="json",
        )
        assert resp.status_code == 201
        assert "access_token" in resp.cookies
        assert "refresh_token" in resp.cookies
        assert resp.data["user"]["email"] == "new@example.com"

    def test_duplicate_email_returns_400(self, api_client):
        UserFactory(email="dupe@example.com")
        resp = api_client.post(
            reverse("auth:register"),
            {
                "email": "dupe@example.com",
                "password": "S3curePass!9",
                "first_name": "D",
                "last_name": "U",
            },
            format="json",
        )
        assert resp.status_code == 400

    def test_weak_password_returns_400(self, api_client):
        resp = api_client.post(
            reverse("auth:register"),
            {
                "email": "weak@example.com",
                "password": "123",
                "first_name": "W",
                "last_name": "K",
            },
            format="json",
        )
        assert resp.status_code == 400


@pytest.mark.django_db
class TestCookieAuth:
    def test_stale_cookie_does_not_block_public_endpoint(self, api_client):
        # A leftover/invalid access_token cookie must not 401 register (AllowAny).
        api_client.cookies["access_token"] = "invalid.token.value"
        resp = api_client.post(
            reverse("auth:register"),
            {
                "email": "fresh@example.com",
                "password": "S3curePass!9",
                "first_name": "F",
                "last_name": "R",
            },
            format="json",
        )
        assert resp.status_code == 201

    def test_stale_cookie_still_401s_protected_endpoint(self, api_client):
        api_client.cookies["access_token"] = "invalid.token.value"
        resp = api_client.get(reverse("auth:me"))
        assert resp.status_code == 401
