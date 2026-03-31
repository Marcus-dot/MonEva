"""
CookieJWTAuthentication — reads the JWT from an httpOnly cookie instead of
the Authorization header. Kept in a separate file so it can be referenced in
REST_FRAMEWORK settings without triggering a circular import.
"""
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken

ACCESS_COOKIE = 'moneva_access'


class CookieJWTAuthentication(JWTAuthentication):
    """Read JWT from the httpOnly access cookie instead of Authorization header."""

    def authenticate(self, request):
        raw_token = request.COOKIES.get(ACCESS_COOKIE)
        if raw_token is None:
            return None
        try:
            validated_token = self.get_validated_token(raw_token)
        except InvalidToken:
            return None
        return self.get_user(validated_token), validated_token
