"""Auth endpoint tests."""

from unittest.mock import patch

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
    def test_new_email_returns_202_unverified(self, api_client):
        with patch("apps.users.tasks.send_verification_email.delay") as send:
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
        assert resp.status_code == 202
        assert "access_token" not in resp.cookies  # no auto-login until verified
        from apps.users.models import User

        u = User.objects.get(email="new@example.com")
        assert u.email_verified is False
        assert send.called

    def test_existing_email_same_neutral_response(self, api_client):
        UserFactory(email="dupe@example.com")
        with patch("apps.users.tasks.send_already_registered_email.delay") as nudge:
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
        # Identical to a brand-new email (202) — no enumeration leak.
        assert resp.status_code == 202
        assert nudge.called  # owner nudged by email instead of leaking existence

    def test_honeypot_blocks_silently(self, api_client):
        with patch("apps.users.tasks.send_verification_email.delay") as send:
            resp = api_client.post(
                reverse("auth:register"),
                {
                    "email": "bot@example.com",
                    "password": "S3curePass!9",
                    "first_name": "B",
                    "last_name": "T",
                    "website": "http://spam.example",
                },
                format="json",
            )
        assert resp.status_code == 202  # looks like success to the bot
        from apps.users.models import User

        assert not User.objects.filter(email="bot@example.com").exists()
        assert not send.called

    def test_disposable_email_blocked(self, api_client):
        resp = api_client.post(
            reverse("auth:register"),
            {
                "email": "x@mailinator.com",
                "password": "S3curePass!9",
                "first_name": "X",
                "last_name": "Y",
            },
            format="json",
        )
        assert resp.status_code == 400

    def test_disposable_subdomain_blocked(self, api_client):
        # sub.mailinator.com must be caught via the parent-domain check.
        resp = api_client.post(
            reverse("auth:register"),
            {
                "email": "x@sub.mailinator.com",
                "password": "S3curePass!9",
                "first_name": "X",
                "last_name": "Y",
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
        with patch("apps.users.tasks.send_verification_email.delay"):
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
        assert resp.status_code == 202

    def test_stale_cookie_still_401s_protected_endpoint(self, api_client):
        api_client.cookies["access_token"] = "invalid.token.value"
        resp = api_client.get(reverse("auth:me"))
        assert resp.status_code == 401


@pytest.mark.django_db
class TestRefresh:
    def test_rotates_and_blacklists_old(self, api_client):
        UserFactory(email="rot@example.com", password="testpass123")
        login = api_client.post(
            reverse("auth:login"),
            {"email": "rot@example.com", "password": "testpass123"},
            format="json",
        )
        old_refresh = login.cookies["refresh_token"].value

        api_client.cookies["refresh_token"] = old_refresh
        r1 = api_client.post(reverse("auth:refresh"))
        assert r1.status_code == 200
        new_refresh = r1.cookies["refresh_token"].value
        assert new_refresh and new_refresh != old_refresh  # rotated

        # Reusing the OLD refresh token is now rejected (blacklisted).
        api_client.cookies["refresh_token"] = old_refresh
        r2 = api_client.post(reverse("auth:refresh"))
        assert r2.status_code == 401


@pytest.mark.django_db
class TestEmailVerification:
    def test_unverified_cannot_login(self, api_client):
        UserFactory(
            email="unv@example.com", password="testpass123", email_verified=False
        )
        resp = api_client.post(
            reverse("auth:login"),
            {"email": "unv@example.com", "password": "testpass123"},
            format="json",
        )
        assert resp.status_code == 400

    def test_verify_token_activates(self, api_client):
        from apps.users.tokens import make_email_verify_token

        u = UserFactory(email="ver@example.com", email_verified=False)
        resp = api_client.post(
            reverse("auth:verify-email"),
            {"token": make_email_verify_token(u.pk)},
            format="json",
        )
        assert resp.status_code == 200
        u.refresh_from_db()
        assert u.email_verified is True

    def test_verify_bad_token_400(self, api_client):
        resp = api_client.post(
            reverse("auth:verify-email"), {"token": "garbage"}, format="json"
        )
        assert resp.status_code == 400


@pytest.mark.django_db
class TestPasswordReset:
    def test_forgot_is_neutral_for_unknown_email(self, api_client):
        resp = api_client.post(
            reverse("auth:forgot-password"),
            {"email": "nobody@example.com"},
            format="json",
        )
        assert resp.status_code == 202

    def test_reset_flow_sets_new_password(self, api_client):
        from django.contrib.auth.tokens import default_token_generator

        u = UserFactory(email="reset@example.com", password="oldpass123")
        token = default_token_generator.make_token(u)
        resp = api_client.post(
            reverse("auth:reset-password"),
            {"uid": str(u.pk), "token": token, "new_password": "N3wStrongPass!"},
            format="json",
        )
        assert resp.status_code == 200
        u.refresh_from_db()
        assert u.check_password("N3wStrongPass!")

    def test_reset_bad_token_400(self, api_client):
        u = UserFactory(email="reset2@example.com")
        resp = api_client.post(
            reverse("auth:reset-password"),
            {"uid": str(u.pk), "token": "bad", "new_password": "N3wStrongPass!"},
            format="json",
        )
        assert resp.status_code == 400


@pytest.mark.django_db
class TestTwoFactor:
    def _device(self, user, confirmed=True):
        from django_otp.plugins.otp_totp.models import TOTPDevice

        return TOTPDevice.objects.create(
            user=user, name="default", confirmed=confirmed
        )

    def _code(self, device):
        from django_otp.oath import totp

        return str(totp(device.bin_key)).zfill(6)

    def test_setup_returns_otpauth_url(self, user_client):
        resp = user_client.post(reverse("auth:2fa-setup"))
        assert resp.status_code == 200
        assert resp.json()["otpauth_url"].startswith("otpauth://")

    def test_confirm_enables_device(self, user_client, user):
        device = self._device(user, confirmed=False)
        resp = user_client.post(
            reverse("auth:2fa-confirm"),
            {"code": self._code(device)},
            format="json",
        )
        assert resp.status_code == 200
        device.refresh_from_db()
        assert device.confirmed is True

    def test_login_with_2fa_requires_second_step(self, api_client, user):
        self._device(user, confirmed=True)
        resp = api_client.post(
            reverse("auth:login"),
            {"email": user.email, "password": "testpass123"},
            format="json",
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("requires_2fa") is True
        assert body.get("pre_auth_token")
        assert "access_token" not in resp.cookies  # no JWT until verified

    def test_verify_completes_login(self, api_client, user):
        device = self._device(user, confirmed=True)
        login = api_client.post(
            reverse("auth:login"),
            {"email": user.email, "password": "testpass123"},
            format="json",
        )
        resp = api_client.post(
            reverse("auth:2fa-verify"),
            {
                "pre_auth_token": login.json()["pre_auth_token"],
                "code": self._code(device),
            },
            format="json",
        )
        assert resp.status_code == 200
        assert "access_token" in resp.cookies

    def test_verify_bad_code_rejected(self, api_client, user):
        self._device(user, confirmed=True)
        login = api_client.post(
            reverse("auth:login"),
            {"email": user.email, "password": "testpass123"},
            format="json",
        )
        resp = api_client.post(
            reverse("auth:2fa-verify"),
            {"pre_auth_token": login.json()["pre_auth_token"], "code": "000000"},
            format="json",
        )
        assert resp.status_code == 400

    def test_disable_removes_device(self, user_client, user):
        from django_otp.plugins.otp_totp.models import TOTPDevice

        self._device(user, confirmed=True)
        resp = user_client.post(
            reverse("auth:2fa-disable"),
            {"password": "testpass123"},
            format="json",
        )
        assert resp.status_code == 200
        assert not TOTPDevice.objects.filter(user=user).exists()

    def test_lockout_after_repeated_failures(self, api_client, user):
        self._device(user, confirmed=True)
        login = api_client.post(
            reverse("auth:login"),
            {"email": user.email, "password": "testpass123"},
            format="json",
        )
        pre = login.json()["pre_auth_token"]
        for _ in range(5):
            api_client.post(
                reverse("auth:2fa-verify"),
                {"pre_auth_token": pre, "code": "000000"},
                format="json",
            )
        # 6th attempt is locked out per-account, regardless of source IP.
        resp = api_client.post(
            reverse("auth:2fa-verify"),
            {"pre_auth_token": pre, "code": "000000"},
            format="json",
        )
        assert resp.status_code == 429
