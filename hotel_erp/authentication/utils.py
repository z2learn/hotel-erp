from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import CustomUser
import logging

logger = logging.getLogger(__name__)

def send_guest_credentials_email(guest_user, booking_duration):
    """Send guest credentials via email"""
    try:
        subject = 'Hotel Access Credentials'
        html_message = render_to_string('authentication/emails/guest_credentials.html', {
            'guest_user': guest_user,
            'booking_duration': booking_duration,
            'login_url': f'{settings.SITE_URL}/authentication/login/'
        })
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[guest_user.email],
            html_message=html_message
        )
        logger.info(f"Guest credentials email sent to {guest_user.email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send guest credentials email: {str(e)}")
        return False

def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def is_staff_user(user):
    """Check if user is staff (admin, reception, maintenance)"""
    return user.role in ['admin', 'reception', 'maintenance']

def get_user_permissions(user):
    """Get user permissions based on role"""
    permissions = {
        'can_create_staff': False,
        'can_create_guest': False,
        'can_view_reports': False,
        'can_manage_system': False,
    }
    
    if user.role == 'admin':
        permissions.update({
            'can_create_staff': True,
            'can_create_guest': True,
            'can_view_reports': True,
            'can_manage_system': True,
        })
    elif user.role == 'reception':
        permissions.update({
            'can_create_guest': True,
            'can_view_reports': True,
        })
    
    return permissions