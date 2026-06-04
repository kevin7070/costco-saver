"""Cookie-based JWT authentication.

Reads the `access_token` cookie (set by LoginView/RefreshView) instead
of the Authorization header. Falls back to the header-based JWT for
mobile/API clients.
"""

from rest_framework_simplejwt.authentication import JWTAuthentication


class CookieJWTAuthentication(JWTAuthentication):
    """JWT authentication via HttpOnly cookie."""

    def authenticate(self, request):
        token = request.COOKIES.get("access_token")
        if not token:
            return None
        validated_token = self.get_validated_token(token)
        return (self.get_user(validated_token), validated_token)
