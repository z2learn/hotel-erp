from django import template
from django.contrib.auth import get_user_model

register = template.Library()
User = get_user_model()

@register.simple_tag
def get_user_role_display(role):
    """Get display name for user role"""
    role_dict = dict(User.ROLE_CHOICES)
    return role_dict.get(role, role)

@register.inclusion_tag('authentication/partials/user_info.html')
def show_user_info(user):
    """Show user information"""
    return {'user': user}

@register.filter
def is_role(user, role):
    """Check if user has specific role"""
    return user.role == role if hasattr(user, 'role') else False

@register.simple_tag
def get_dashboard_url(role):
    """Get dashboard URL for role"""
    role_urls = {
        'admin': '/admin-dashboard/',
        'reception': '/reception-dashboard/',
        'maintenance': '/maintenance-dashboard/',
        'guest': '/guest-portal/'
    }
    return role_urls.get(role, '/')
