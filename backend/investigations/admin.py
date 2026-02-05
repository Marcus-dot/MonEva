from django.contrib import admin
from .models import Investigation, InvestigationUpdate, InvestigationEvidence, InvestigationNote


@admin.register(Investigation)
class InvestigationAdmin(admin.ModelAdmin):
    list_display = ['title', 'status', 'severity', 'category', 'project', 'assigned_to', 'opened_at']
    list_filter = ['status', 'severity', 'category', 'opened_at']
    search_fields = ['title', 'description', 'tags']
    readonly_fields = ['opened_at', 'resolved_at', 'closed_at', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Info', {
            'fields': ('title', 'description', 'category', 'severity', 'status')
        }),
        ('Relationships', {
            'fields': ('project', 'triggered_by_inspection', 'related_grievance', 'assigned_to', 'created_by')
        }),
        ('Dates', {
            'fields': ('opened_at', 'target_resolution_date', 'resolved_at', 'closed_at')
        }),
        ('Resolution', {
            'fields': ('resolution_summary', 'corrective_actions')
        }),
        ('Metadata', {
            'fields': ('tags', 'estimated_impact', 'created_at', 'updated_at')
        }),
    )


@admin.register(InvestigationUpdate)
class InvestigationUpdateAdmin(admin.ModelAdmin):
    list_display = ['investigation', 'update_type', 'created_by', 'created_at']
    list_filter = ['update_type', 'created_at']
    readonly_fields = ['created_at']
    search_fields = ['content']


@admin.register(InvestigationEvidence)
class InvestigationEvidenceAdmin(admin.ModelAdmin):
    list_display = ['investigation', 'evidence', 'added_by', 'added_at']
    list_filter = ['added_at']
    readonly_fields = ['added_at']


@admin.register(InvestigationNote)
class InvestigationNoteAdmin(admin.ModelAdmin):
    list_display = ['investigation', 'author', 'is_internal', 'created_at']
    list_filter = ['is_internal', 'created_at']
    readonly_fields = ['created_at']
