from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Organization

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('role',)}),
    )

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'type')
    search_fields = ('name',)
