"""
Cookie-based JWT authentication for MonEva.

Replaces localStorage token storage with httpOnly cookies, protecting
against XSS attacks. SameSite=Lax guards against CSRF.

Endpoints (registered in urls.py):
  POST /api/v1/auth/login/   → sets access + refresh cookies, returns user info
  POST /api/v1/auth/logout/  → clears both cookies
  POST /api/v1/auth/refresh/ → uses refresh cookie to issue new access cookie
"""

import logging
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from core.authentication import ACCESS_COOKIE

logger = logging.getLogger(__name__)

REFRESH_COOKIE = 'moneva_refresh'


def _cookie_kwargs(max_age: int) -> dict:
    return {
        'max_age': max_age,
        'httponly': True,
        'secure': not settings.DEBUG,   # HTTPS-only in production
        'samesite': 'Lax',
        'path': '/',
    }


def _set_auth_cookies(response, access_token: str, refresh_token: str):
    jwt = settings.SIMPLE_JWT
    response.set_cookie(
        ACCESS_COOKIE,
        str(access_token),
        **_cookie_kwargs(int(jwt['ACCESS_TOKEN_LIFETIME'].total_seconds())),
    )
    response.set_cookie(
        REFRESH_COOKIE,
        str(refresh_token),
        **_cookie_kwargs(int(jwt['REFRESH_TOKEN_LIFETIME'].total_seconds())),
    )


def _clear_auth_cookies(response):
    response.delete_cookie(ACCESS_COOKIE, path='/')
    response.delete_cookie(REFRESH_COOKIE, path='/')


class CookieLoginView(APIView):
    """POST /api/v1/auth/login/ — authenticate and set httpOnly JWT cookies."""
    permission_classes = [permissions.AllowAny]
    throttle_scope = 'login'

    def post(self, request):
        from django.contrib.auth import authenticate
        username = request.data.get('username', '').strip()
        password = request.data.get('password', '')

        if not username or not password:
            return Response(
                {'detail': 'Username and password are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response(
                {'detail': 'Invalid credentials.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_active:
            return Response(
                {'detail': 'Account is disabled.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        refresh = RefreshToken.for_user(user)
        response = Response({
            'id': str(user.id),
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role.name if user.role else None,
            'is_admin': user.is_admin_user,
        })
        _set_auth_cookies(response, refresh.access_token, refresh)
        logger.info('User %s logged in', user.username)
        return response


class CookieRefreshView(APIView):
    """POST /api/v1/auth/refresh/ — issue new access cookie from refresh cookie."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        raw_refresh = request.COOKIES.get(REFRESH_COOKIE)
        if not raw_refresh:
            return Response(
                {'detail': 'No refresh token.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        try:
            refresh = RefreshToken(raw_refresh)
            new_access = refresh.access_token
        except TokenError as e:
            return Response({'detail': str(e)}, status=status.HTTP_401_UNAUTHORIZED)

        response = Response({'detail': 'Token refreshed.'})
        jwt = settings.SIMPLE_JWT
        response.set_cookie(
            ACCESS_COOKIE,
            str(new_access),
            **_cookie_kwargs(int(jwt['ACCESS_TOKEN_LIFETIME'].total_seconds())),
        )
        return response


class CookieLogoutView(APIView):
    """POST /api/v1/auth/logout/ — blacklist refresh token and clear cookies."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        raw_refresh = request.COOKIES.get(REFRESH_COOKIE)
        if raw_refresh:
            try:
                token = RefreshToken(raw_refresh)
                token.blacklist()
            except Exception:
                pass  # Already expired or invalid — still clear cookies

        response = Response({'detail': 'Logged out.'})
        _clear_auth_cookies(response)
        return response
