"""Auth endpoints — login, logout, refresh, me, change-password."""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from . import tasks
from .serializers import (
    ChangePasswordSerializer,
    ForgotPasswordSerializer,
    LoginSerializer,
    RegisterSerializer,
    ResendVerificationSerializer,
    ResetPasswordSerializer,
    TwoFactorConfirmSerializer,
    TwoFactorDisableSerializer,
    TwoFactorVerifySerializer,
    UserSerializer,
)
from .tokens import (
    make_pre_auth_token,
    read_email_verify_token,
    read_pre_auth_token,
)


def _set_jwt_cookies(response, access_token: str, refresh_token: str) -> None:
    response.set_cookie(
        "access_token",
        access_token,
        httponly=True,
        secure=settings.JWT_COOKIE_SECURE,
        samesite=settings.JWT_COOKIE_SAMESITE,
        path=settings.JWT_COOKIE_PATH,
        max_age=int(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds()),
    )
    response.set_cookie(
        "refresh_token",
        refresh_token,
        httponly=True,
        secure=settings.JWT_COOKIE_SECURE,
        samesite=settings.JWT_COOKIE_SAMESITE,
        path=settings.JWT_COOKIE_PATH,
        max_age=int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()),
    )


def _has_confirmed_totp(user) -> bool:
    from django_otp.plugins.otp_totp.models import TOTPDevice

    return TOTPDevice.objects.filter(user=user, confirmed=True).exists()


def _login_response(user) -> Response:
    refresh = RefreshToken.for_user(user)
    response = Response({"user": UserSerializer(user).data}, status=status.HTTP_200_OK)
    _set_jwt_cookies(response, str(refresh.access_token), str(refresh))
    return response


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "auth_login"

    def post(self, request):
        # Pass request so AxesBackend can record the login attempt.
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        # With a confirmed TOTP device, defer JWT until the second step.
        if _has_confirmed_totp(user):
            return Response(
                {"requires_2fa": True, "pre_auth_token": make_pre_auth_token(user.pk)},
                status=status.HTTP_200_OK,
            )
        return _login_response(user)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except TokenError:
                pass  # invalid/expired token is fine on logout

        response = Response(status=status.HTTP_204_NO_CONTENT)
        response.delete_cookie("access_token", path=settings.JWT_COOKIE_PATH)
        response.delete_cookie("refresh_token", path=settings.JWT_COOKIE_PATH)
        return response


class RefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        raw = request.COOKIES.get("refresh_token") or request.data.get("refresh")
        if not raw:
            return Response(
                {"detail": "No refresh token provided."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        # TokenRefreshSerializer handles rotation + blacklist-after-rotation per
        # SIMPLE_JWT settings: validated_data carries a fresh "refresh" and the
        # old one is blacklisted, so a leaked refresh token is single-use.
        serializer = TokenRefreshSerializer(data={"refresh": raw})
        try:
            serializer.is_valid(raise_exception=True)
        except (InvalidToken, TokenError):
            return Response(
                {"detail": "Token is invalid or expired."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        data = serializer.validated_data
        new_refresh = data.get("refresh", raw)  # rotated token, or same if off
        response = Response({"access": data["access"]}, status=status.HTTP_200_OK)
        _set_jwt_cookies(response, data["access"], new_refresh)
        return response


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_scope = "password_change"

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save()
        return Response({"detail": "Password changed."}, status=status.HTTP_200_OK)


_REGISTER_NEUTRAL = {
    "detail": "Check your inbox to verify your email and finish signing up."
}


class RegisterView(APIView):
    """Public self-service registration — enumeration-safe.

    Returns an identical response whether the email is new or already registered.
    New → create unverified + send a verification email. Existing → nudge the
    owner by email. No auto-login until the email is verified.
    """

    permission_classes = [AllowAny]
    throttle_scope = "register"

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Honeypot filled → bot. Respond like success, do nothing.
        if data.get("website"):
            return Response(_REGISTER_NEUTRAL, status=status.HTTP_202_ACCEPTED)

        email = data["email"]
        User = get_user_model()
        if not User.objects.filter(email=email).exists():
            user = User.objects.create_user(
                email=email,
                password=data["password"],
                first_name=data["first_name"],
                last_name=data["last_name"],
            )
            tasks.send_verification_email.delay(str(user.pk))
        else:
            # Constant-time: do equivalent password-hash work so response timing
            # doesn't reveal that the email already exists.
            User().set_password(data["password"])
            tasks.send_already_registered_email.delay(email)

        return Response(_REGISTER_NEUTRAL, status=status.HTTP_202_ACCEPTED)


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        uid = read_email_verify_token(request.data.get("token", ""))
        User = get_user_model()
        user = User.objects.filter(pk=uid).first() if uid else None
        if user is None:
            return Response(
                {"detail": "Invalid or expired verification link."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not user.email_verified:
            user.email_verified = True
            user.save(update_fields=["email_verified"])
        return Response({"detail": "Email verified. You can now log in."})


class ResendVerificationView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "register"

    def post(self, request):
        serializer = ResendVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].lower().strip()
        User = get_user_model()
        user = User.objects.filter(email=email, email_verified=False).first()
        if user is not None:
            tasks.send_verification_email.delay(str(user.pk))
        return Response(
            {"detail": "If that email needs verification, a new link is on its way."},
            status=status.HTTP_202_ACCEPTED,
        )


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "password_reset"

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].lower().strip()
        User = get_user_model()
        user = User.objects.filter(email=email).first()
        if user is not None:
            token = default_token_generator.make_token(user)
            tasks.send_password_reset_email.delay(str(user.pk), token)
        return Response(
            {"detail": "If that email exists, a reset link is on its way."},
            status=status.HTTP_202_ACCEPTED,
        )


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "password_reset"

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        User = get_user_model()
        user = User.objects.filter(pk=data["uid"]).first()
        if user is None or not default_token_generator.check_token(user, data["token"]):
            return Response(
                {"detail": "Invalid or expired reset link."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.set_password(data["new_password"])
        # A successful reset proves email ownership, so mark it verified too.
        user.email_verified = True
        user.save(update_fields=["password", "email_verified"])
        # Clear any axes lockout for this account (locked-out users can recover).
        try:
            from axes.utils import reset

            reset(username=user.email)
        except Exception:  # noqa: BLE001 — axes disabled in tests
            pass
        return Response({"detail": "Password reset. You can now log in."})


class TwoFactorSetupView(APIView):
    """Start enrollment: create an unconfirmed TOTP device, return its otpauth URI."""

    permission_classes = [IsAuthenticated]
    throttle_scope = "password_change"

    def post(self, request):
        from django_otp.plugins.otp_totp.models import TOTPDevice

        # Drop any prior pending setup, then issue a fresh secret.
        TOTPDevice.objects.filter(user=request.user, confirmed=False).delete()
        device = TOTPDevice.objects.create(
            user=request.user, name="default", confirmed=False
        )
        return Response({"otpauth_url": device.config_url})


class TwoFactorConfirmView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TwoFactorConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        from django_otp.plugins.otp_totp.models import TOTPDevice

        device = TOTPDevice.objects.filter(user=request.user, confirmed=False).first()
        if device is None:
            return Response(
                {"detail": "No pending 2FA setup. Start setup first."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not device.verify_token(serializer.validated_data["code"]):
            return Response({"detail": "Invalid code."}, status=status.HTTP_400_BAD_REQUEST)
        device.confirmed = True
        device.save()
        return Response({"detail": "Two-factor authentication enabled."})


class TwoFactorDisableView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TwoFactorDisableSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not request.user.check_password(serializer.validated_data["password"]):
            return Response(
                {"detail": "Password is incorrect."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        from django_otp.plugins.otp_totp.models import TOTPDevice

        TOTPDevice.objects.filter(user=request.user).delete()
        return Response({"detail": "Two-factor authentication disabled."})


class TwoFactorVerifyView(APIView):
    """Second login step: pre-auth token + TOTP code -> JWT."""

    permission_classes = [AllowAny]
    throttle_scope = "auth_login"

    def post(self, request):
        serializer = TwoFactorVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        uid = read_pre_auth_token(serializer.validated_data["pre_auth_token"])
        User = get_user_model()
        user = User.objects.filter(pk=uid).first() if uid else None
        if user is None:
            return Response(
                {"detail": "Invalid or expired session. Log in again."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Per-account lockout caps TOTP guessing even across many IPs (a per-IP
        # throttle alone is bypassable with a botnet).
        from django.core.cache import cache

        fail_key = f"2fa-fail:{user.pk}"
        if cache.get(fail_key, 0) >= 5:
            return Response(
                {"detail": "Too many attempts. Please log in again later."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        from django_otp.plugins.otp_totp.models import TOTPDevice

        device = TOTPDevice.objects.filter(user=user, confirmed=True).first()
        if device is None or not device.verify_token(serializer.validated_data["code"]):
            cache.set(fail_key, cache.get(fail_key, 0) + 1, timeout=900)
            return Response({"detail": "Invalid code."}, status=status.HTTP_400_BAD_REQUEST)
        cache.delete(fail_key)
        return _login_response(user)
