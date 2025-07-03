from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Booking, GuestCredentials

@receiver(post_save, sender=Booking)
def create_guest_credentials(sender, instance, created, **kwargs):
    """
    Automatically create guest credentials when a booking is confirmed
    """
    if created and instance.booking_status == 'confirmed':
        # Create guest credentials
        GuestCredentials.objects.get_or_create(
            booking=instance,
            defaults={
                'username': instance.guest_email,
                'password': instance.guest_phone,
                'is_active': True,
                'expires_at': timezone.make_aware(
                    timezone.datetime.combine(
                        instance.check_out_date, 
                        timezone.datetime.min.time()
                    )
                )
            }
        )

@receiver(post_save, sender=Booking)
def update_guest_credentials_status(sender, instance, **kwargs):
    """
    Update guest credentials status based on booking status
    """
    try:
        guest_cred = GuestCredentials.objects.get(booking=instance)
        
        if instance.booking_status in ['checked_out', 'cancelled']:
            guest_cred.is_active = False
            guest_cred.save()
        elif instance.booking_status in ['confirmed', 'checked_in']:
            guest_cred.is_active = True
            guest_cred.save()
            
    except GuestCredentials.DoesNotExist:
        # If credentials don't exist and booking is confirmed, create them
        if instance.booking_status == 'confirmed':
            GuestCredentials.objects.create(
                booking=instance,
                username=instance.guest_email,
                password=instance.guest_phone,
                is_active=True,
                expires_at=timezone.make_aware(
                    timezone.datetime.combine(
                        instance.check_out_date, 
                        timezone.datetime.min.time()
                    )
                )
            )