from django.contrib import admin
from .models import Grievance

@admin.register(Grievance)
class GrievanceAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'status', 'resolution_date')
    list_filter = ('status',)
