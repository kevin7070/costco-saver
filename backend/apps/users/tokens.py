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
