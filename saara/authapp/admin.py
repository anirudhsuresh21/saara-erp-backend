from django.contrib import admin
from .models import (
    AllowedEmailDomain, User, UserSession, AuditLog
)


@admin.register(AllowedEmailDomain)
class AllowedEmailDomainAdmin(admin.ModelAdmin):
    """Admin interface for managing allowed email domains"""
    list_display = ['domain', 'institution_name', 'allow_subdomains', 'is_active', 'created_at']
    list_filter = ['is_active', 'allow_subdomains', 'created_at']
    search_fields = ['domain', 'institution_name']
    ordering = ['domain']
    
    fieldsets = (
        ('Domain Information', {
            'fields': ('domain', 'institution_name')
        }),
        ('Settings', {
            'fields': ('is_active', 'allow_subdomains'),
            'description': 'Allow subdomains enables emails like user@siescoms.sies.edu.in for domain sies.edu.in'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def has_delete_permission(self, request, obj=None):
        # Only superusers can delete domains
        return request.user.is_superuser
    
    def has_add_permission(self, request):
        # Only superusers can add domains
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        # Only superusers can change domains
        return request.user.is_superuser


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'role', 'is_active', 'created_at', 'last_login']
    list_filter = ['role', 'is_active', 'created_at']
    search_fields = ['email']
    readonly_fields = ['user_id', 'created_at', 'last_login']

# admin.site.register(Admin)
admin.site.register(UserSession)
admin.site.register(AuditLog)
