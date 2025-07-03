from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.db.models import Q
from .models import CustomUser, UserSession, LoginAttempt
from .forms import StaffUserCreationForm

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    add_form = StaffUserCreationForm
    form = StaffUserCreationForm
    
    # List display configuration
    list_display = (
        'username', 'email', 'first_name', 'last_name', 
        'role', 'is_active', 'is_temporary', 'employee_id',
        'created_at', 'expires_status'
    )
    
    list_filter = (
        'role', 'is_active', 'is_staff', 'is_temporary', 
        'date_joined', 'department'
    )
    
    search_fields = (
        'username', 'email', 'first_name', 'last_name', 
        'employee_id', 'phone'
    )
    
    ordering = ('-date_joined',)
    
    # Fieldsets for editing existing users
    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'email', 'phone')
        }),
        ('Role & Employment', {
            'fields': ('role', 'employee_id', 'department', 'created_by')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Temporary Access', {
            'fields': ('is_temporary', 'expires_at'),
            'classes': ('collapse',)
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    
    # Fieldsets for adding new users
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'email', 'phone')
        }),
        ('Role & Employment', {
            'fields': ('role', 'employee_id', 'department')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff'),
        }),
    )
    
    readonly_fields = ('date_joined', 'last_login')
    
    # Custom methods for list display
    def created_at(self, obj):
        return obj.date_joined.strftime('%Y-%m-%d %H:%M')
    created_at.short_description = 'Created At'
    created_at.admin_order_field = 'date_joined'
    
    def expires_status(self, obj):
        if not obj.is_temporary:
            return format_html('<span style="color: green;">✓ Permanent</span>')
        elif obj.is_expired():
            return format_html('<span style="color: red;">✗ Expired</span>')
        else:
            return format_html('<span style="color: orange;">⏳ Temporary</span>')
    expires_status.short_description = 'Status'
    
    # Custom actions
    actions = ['activate_users', 'deactivate_users', 'delete_expired_guests']
    
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} users were successfully activated.')
    activate_users.short_description = "Activate selected users"
    
    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} users were successfully deactivated.')
    deactivate_users.short_description = "Deactivate selected users"
    
    def delete_expired_guests(self, request, queryset):
        expired_guests = queryset.filter(
            is_temporary=True,
            expires_at__lt=timezone.now()
        )
        count = expired_guests.count()
        expired_guests.delete()
        self.message_user(request, f'{count} expired guest accounts were deleted.')
    delete_expired_guests.short_description = "Delete expired guest accounts"
    
    # Override get_queryset to optimize database queries
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by')
    
    # Custom save method
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new user
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'session_key', 'login_time', 'logout_time', 
        'ip_address', 'is_active', 'session_duration'
    )
    
    list_filter = (
        'is_active', 'login_time', 'user__role'
    )
    
    search_fields = (
        'user__username', 'user__email', 'ip_address', 'session_key'
    )
    
    readonly_fields = (
        'user', 'session_key', 'login_time', 'logout_time', 
        'ip_address', 'user_agent', 'session_duration'
    )
    
    ordering = ('-login_time',)
    
    # Custom methods
    def session_duration(self, obj):
        if obj.logout_time:
            duration = obj.logout_time - obj.login_time
            hours, remainder = divmod(duration.total_seconds(), 3600)
            minutes, _ = divmod(remainder, 60)
            return f"{int(hours)}h {int(minutes)}m"
        elif obj.is_active:
            duration = timezone.now() - obj.login_time
            hours, remainder = divmod(duration.total_seconds(), 3600)
            minutes, _ = divmod(remainder, 60)
            return f"{int(hours)}h {int(minutes)}m (Active)"
        return "Unknown"
    session_duration.short_description = 'Duration'
    
    # Actions
    actions = ['terminate_sessions']
    
    def terminate_sessions(self, request, queryset):
        updated = queryset.filter(is_active=True).update(
            is_active=False, 
            logout_time=timezone.now()
        )
        self.message_user(request, f'{updated} active sessions were terminated.')
    terminate_sessions.short_description = "Terminate selected sessions"
    
    def has_add_permission(self, request):
        # Prevent manual session creation
        return False
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = (
        'username', 'ip_address', 'attempted_at', 'success', 
        'user_agent_short', 'attempt_status'
    )
    
    list_filter = (
        'success', 'attempted_at'
    )
    
    search_fields = (
        'username', 'ip_address'
    )
    
    readonly_fields = (
        'username', 'ip_address', 'attempted_at', 'success', 'user_agent'
    )
    
    ordering = ('-attempted_at',)
    
    # Custom methods
    def user_agent_short(self, obj):
        if len(obj.user_agent) > 50:
            return obj.user_agent[:50] + '...'
        return obj.user_agent
    user_agent_short.short_description = 'User Agent'
    
    def attempt_status(self, obj):
        if obj.success:
            return format_html('<span style="color: green;">✓ Success</span>')
        else:
            return format_html('<span style="color: red;">✗ Failed</span>')
    attempt_status.short_description = 'Status'
    
    def has_add_permission(self, request):
        # Prevent manual login attempt creation
        return False
    
    def has_change_permission(self, request, obj=None):
        # Prevent editing login attempts
        return False

# Custom admin site configuration
admin.site.site_header = 'Hotel ERP Administration'
admin.site.site_title = 'Hotel ERP Admin'
admin.site.index_title = 'Hotel ERP Management System'

# Register additional configurations
class AuthenticationAdminConfig:
    """Configuration class for authentication admin"""
    
    @staticmethod
    def get_admin_stats():
        """Get statistics for admin dashboard"""
        from django.db.models import Count
        
        stats = {
            'total_users': CustomUser.objects.count(),
            'active_users': CustomUser.objects.filter(is_active=True).count(),
            'staff_users': CustomUser.objects.filter(role__in=['admin', 'reception', 'maintenance']).count(),
            'guest_users': CustomUser.objects.filter(role='guest').count(),
            'expired_guests': CustomUser.objects.filter(
                is_temporary=True,
                expires_at__lt=timezone.now()
            ).count(),
            'active_sessions': UserSession.objects.filter(is_active=True).count(),
            'recent_login_attempts': LoginAttempt.objects.filter(
                attempted_at__gte=timezone.now() - timezone.timedelta(hours=24)
            ).count(),
        }
        
        return stats