"""Cookie-based JWT authentication.

Reads the `access_token` cookie (set by LoginView/RefreshView) instead
of the Authorization header. Falls back to the header-based JWT for
mobile/API clients.
"""

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError


class CookieJWTAuthentication(JWTAuthentication):
    """JWT authentication via HttpOnly cookie."""

    def authenticate(self, request):
        token = request.COOKIES.get("access_token")
        if not token:
            return None
        try:
            validated_token = self.get_validated_token(token)
        except (InvalidToken, TokenError):
            # A stale/invalid cookie must not block public endpoints
            # (login/register). Treat it as unauthenticated and let the
            # permission layer 401 anything that actually requires auth.
            return None
        return (self.get_user(validated_token), validated_token)
