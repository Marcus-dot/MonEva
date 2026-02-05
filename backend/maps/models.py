from django.db import models
from core.models import User

class ExternalMapLayer(models.Model):
    LAYER_TYPES = [
        ('WMS', 'Web Map Service'),
        ('XYZ', 'XYZ Tile Layer'),
        ('GEOJSON', 'GeoJSON Data'),
    ]

    name = models.CharField(max_length=100)
    layer_type = models.CharField(max_length=10, choices=LAYER_TYPES)
    url = models.URLField(help_text="URL template for tiles or API endpoint for data")
    api_key_env_var = models.CharField(max_length=100, blank=True, null=True, help_text="Environment variable name for the API key (if required)")
    attribution = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.layer_type})"
