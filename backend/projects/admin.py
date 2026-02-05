from django.contrib import admin
from .models import Project, Contract, Milestone

class MilestoneInline(admin.TabularInline):
    model = Milestone
    extra = 0

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'status', 'start_date', 'owner_org')
    list_filter = ('type', 'status', 'owner_org')
    search_fields = ('name',)

@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ('project', 'contractor', 'total_value', 'start_date')
    inlines = [MilestoneInline]

@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    list_display = ('title', 'contract', 'target_percent', 'status', 'due_date')
    list_filter = ('status',)
