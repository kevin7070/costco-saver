"""Signed, expiring tokens for email-based flows (no DB table needed).

Uses Django's signing framework: the token carries the user id + a timestamp,
signed with SECRET_KEY. `loads(max_age=...)` rejects tampered or expired tokens.
"""

from __future__ import annotations

from django.core import signing

_VERIFY_SALT = "users.email-verify"
VERIFY_MAX_AGE = 60 * 60 * 48  # 48 hours


def make_email_verify_token(user_id) -> str:
    return signing.dumps({"uid": str(user_id)}, salt=_VERIFY_SALT)


def read_email_verify_token(token: str, max_age: int = VERIFY_MAX_AGE) -> str | None:
    """Return the user id from a valid token, or None if bad/expired."""
    try:
        data = signing.loads(token, salt=_VERIFY_SALT, max_age=max_age)
    except signing.BadSignature:
        return None
    return data.get("uid")


# --- 2FA two-step login: short-lived token issued after password, before TOTP ---
_2FA_SALT = "users.2fa-pre-auth"
PRE_AUTH_MAX_AGE = 5 * 60  # 5 minutes


def make_pre_auth_token(user_id) -> str:
    return signing.dumps({"uid": str(user_id), "p": "2fa"}, salt=_2FA_SALT)


def read_pre_auth_token(token: str, max_age: int = PRE_AUTH_MAX_AGE) -> str | None:
    try:
        data = signing.loads(token, salt=_2FA_SALT, max_age=max_age)
    except signing.BadSignature:
        return None
    return data.get("uid") if data.get("p") == "2fa" else None
