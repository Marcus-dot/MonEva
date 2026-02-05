from django.contrib import admin
from .models import ExternalMapLayer

@admin.register(ExternalMapLayer)
class ExternalMapLayerAdmin(admin.ModelAdmin):
    list_display = ('name', 'layer_type', 'is_active', 'created_at')
    list_filter = ('layer_type', 'is_active')
    search_fields = ('name', 'url')
