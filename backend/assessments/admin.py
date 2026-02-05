from django.contrib import admin
from .models import Inspection, Evidence

class EvidenceInline(admin.TabularInline):
    model = Evidence
    extra = 0

@admin.register(Inspection)
class InspectionAdmin(admin.ModelAdmin):
    list_display = ('milestone', 'inspector', 'quality_verdict', 'inspected_at')
    list_filter = ('quality_verdict', 'inspected_at')
    inlines = [EvidenceInline]

@admin.register(Evidence)
class EvidenceAdmin(admin.ModelAdmin):
    list_display = ('inspection', 'file_type', 'uploaded_at')
