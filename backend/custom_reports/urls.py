from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CustomReportViewSet

router = DefaultRouter()
router.register(r'', CustomReportViewSet, basename='custom_reports')

urlpatterns = [
    path('', include(router.urls)),
]
