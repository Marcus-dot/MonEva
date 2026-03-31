from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.cookie_auth import CookieLoginView, CookieRefreshView, CookieLogoutView
from rest_framework_simplejwt.views import TokenVerifyView

urlpatterns = [
    path('admin/', admin.site.urls),

    # API V1
    path('api/v1/', include('moneva.api_router')),

    # Cookie-based auth (primary — used by the web app)
    path('api/v1/auth/login/', CookieLoginView.as_view(), name='cookie_login'),
    path('api/v1/auth/refresh/', CookieRefreshView.as_view(), name='cookie_refresh'),
    path('api/v1/auth/logout/', CookieLogoutView.as_view(), name='cookie_logout'),

    # Token verify (stateless, for mobile/API clients if needed)
    path('api/v1/auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    # Djoser user management (password reset, registration, etc.)
    path('api/v1/auth/', include('djoser.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
