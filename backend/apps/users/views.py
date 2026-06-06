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
    UserSerializer,
)
from .tokens import read_email_verify_token


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


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "auth_login"

    def post(self, request):
        # Pass request so AxesBackend can record the login attempt.
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        refresh = RefreshToken.for_user(user)
        response = Response(
            {
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )
        _set_jwt_cookies(response, str(refresh.access_token), str(refresh))
        return response


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
