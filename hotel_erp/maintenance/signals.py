from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import MaintenanceWork

@receiver(post_save, sender=MaintenanceWork)
def update_grievance_status(sender, instance, created, **kwargs):
    """Update grievance status when maintenance work is updated"""
    if instance.work_status == 'completed':
        instance.grievance.status = 'completed'
        instance.grievance.save(update_fields=['status'])
    elif instance.work_status == 'in_progress':
        instance.grievance.status = 'in_progress'
        instance.grievance.save(update_fields=['status'])