from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.utils import timezone
from .models import CustomUser, UserSession, LoginAttempt
import logging

logger = logging.getLogger(__name__)

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Log successful user login"""
    logger.info(f"User {user.username} logged in from {request.META.get('REMOTE_ADDR')}")

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """Log user logout"""
    if user:
        logger.info(f"User {user.username} logged out")

@receiver(post_save, sender=CustomUser)
def user_post_save(sender, instance, created, **kwargs):
    """Handle user creation/update"""
    if created:
        logger.info(f"New user created: {instance.username} with role {instance.role}")

@receiver(pre_delete, sender=CustomUser)
def user_pre_delete(sender, instance, **kwargs):
    """Handle user deletion"""
    logger.info(f"User deleted: {instance.username}")