"""
Django signals for admin_panel app

This module contains signal receivers for handling various
events in the admin panel application.
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings

User = get_user_model()


@receiver(post_save, sender=User)
def user_created_handler(sender, instance, created, **kwargs):
    """
    Handle actions when a new user is created by admin
    
    Args:
        sender: The model class that sent the signal
        instance: The user instance that was saved
        created: Boolean indicating if this is a new record
        **kwargs: Additional keyword arguments
    """
    if created and hasattr(instance, 'user_type') and instance.user_type in ['reception', 'maintenance']:
        # Log user creation for audit purposes
        print(f"New {instance.user_type} user created: {instance.email}")
        
        # Send welcome email (optional)
        # send_welcome_email(instance)


@receiver(post_delete, sender=User)
def user_deleted_handler(sender, instance, **kwargs):
    """
    Handle actions when a user is deleted by admin
    
    Args:
        sender: The model class that sent the signal
        instance: The user instance that was deleted
        **kwargs: Additional keyword arguments
    """
    # Log user deletion for audit purposes
    print(f"User deleted: {instance.email} ({instance.user_type})")


def send_welcome_email(user):
    """
    Send welcome email to newly created staff users
    
    Args:
        user: User instance
    """
    if hasattr(settings, 'EMAIL_HOST') and settings.EMAIL_HOST:
        try:
            send_mail(
                subject='Welcome to Hotel ERP System',
                message=f'Hello {user.full_name},\n\nYour account has been created successfully.\nUsername: {user.email}\n\nPlease contact the administrator for your password.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Failed to send welcome email: {e}")


# You can add more signal receivers here as needed
# For example: handling booking confirmations, maintenance task assignments, etc.