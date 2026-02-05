from django.db import models
from core.models import User
import uuid

class CustomReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    
    # Stores the layout and components configuration
    # Structure example: 
    # {
    #   "layout": [
    #      {"i": "chart-1", "x": 0, "y": 0, "w": 6, "h": 4},
    #      {"i": "table-1", "x": 6, "y": 0, "w": 6, "h": 4}
    #   ],
    #   "components": {
    #      "chart-1": {"type": "BAR_CHART", "dataSource": "projects", "config": {...}},
    #      "table-1": {"type": "TABLE", "dataSource": "finance", "config": {...}}
    #   }
    # }
    layout_config = models.JSONField(default=dict)
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='custom_reports')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    is_public = models.BooleanField(default=False)

    def __str__(self):
        return self.title
