"""Transactional auth emails — plain text + a link to the frontend.

Sent via Celery tasks (apps/users/tasks.py) so they're off the request path.
Dev uses the console backend; prod uses SMTP (env-gated in settings).
"""

from __future__ import annotations

from django.conf import settings
from django.core.mail import send_mail

from .tokens import make_email_verify_token


def _frontend_url(path: str) -> str:
    return f"{settings.FRONTEND_URL.rstrip('/')}{path}"


def send_verification_email(user) -> None:
    link = _frontend_url(f"/verify-email?token={make_email_verify_token(user.pk)}")
    send_mail(
        subject="Verify your Costco Saver account",
        message=(
            "Welcome! Confirm your email to activate your account:\n\n"
            f"{link}\n\nThis link expires in 48 hours."
        ),
        from_email=None,  # DEFAULT_FROM_EMAIL
        recipient_list=[user.email],
    )


def send_already_registered_email(email: str) -> None:
    """Sent when someone registers an existing email (keeps responses uniform)."""
    send_mail(
        subject="You already have a Costco Saver account",
        message=(
            "Someone tried to register with this email. If it was you, just log "
            "in. Forgot your password? Use the reset link on the login page."
        ),
        from_email=None,
        recipient_list=[email],
    )


def send_password_reset_email(user, token: str) -> None:
    link = _frontend_url(f"/reset-password?uid={user.pk}&token={token}")
    send_mail(
        subject="Reset your Costco Saver password",
        message=(
            f"Reset your password here:\n\n{link}\n\n"
            "If you didn't request this, you can ignore this email."
        ),
        from_email=None,
        recipient_list=[user.email],
    )
