# admin_panel/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.utils import timezone
from django.conf import settings

class Room(models.Model):
    ROOM_TYPES = [
        ('SINGLE', 'Single Room'),
        ('DOUBLE', 'Double Room'),
        ('SUITE', 'Suite'),
        ('DELUXE', 'Deluxe Room'),
    ]
    
    room_number = models.CharField(max_length=10, unique=True)
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES)
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)
    is_available = models.BooleanField(default=True)
    max_occupancy = models.IntegerField(default=2)
    amenities = models.TextField(blank=True)
    
    def __str__(self):
        return f"Room {self.room_number} - {self.room_type}"

class Booking(models.Model):
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    guest_name = models.CharField(max_length=100)
    guest_email = models.EmailField()
    guest_phone = models.CharField(max_length=15)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    number_of_guests = models.IntegerField(default=1)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    booking_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')  # Renamed from 'status'
    special_requests = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='admin_bookings')  # Added related_name
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Link to guest user account (created after booking)
    guest_user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='admin_panel_booking_profile')
    
    def __str__(self):
        return f"Booking #{self.id} - {self.guest_name} - Room {self.room.room_number}"
    
    def save(self, *args, **kwargs):
        # Calculate total amount
        if self.check_out_date and self.check_in_date:
            days = (self.check_out_date - self.check_in_date).days
            self.total_amount = self.room.price_per_night * days
        super().save(*args, **kwargs)

class Grievance(models.Model):
    PROBLEM_TYPES = [
        ('ROOM_CLEANLINESS', 'Room Cleanliness'),
        ('AC_HEATING', 'AC/Heating Issue'),
        ('PLUMBING', 'Plumbing Issue'),
        ('ELECTRICAL', 'Electrical Issue'),
        ('NOISE', 'Noise Complaint'),
        ('ROOM_SERVICE', 'Room Service'),
        ('WIFI', 'WiFi/Internet Issue'),
        ('MAINTENANCE', 'General Maintenance'),
        ('OTHERS', 'Others'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CLOSED', 'Closed'),
    ]
    
    guest = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
                             limit_choices_to={'role': 'GUEST'}, related_name='admin_grievances')  # Added related_name
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)
    problem_type = models.CharField(max_length=50, choices=PROBLEM_TYPES)
    detailed_description = models.TextField()
    attachment = models.ImageField(upload_to='grievance_attachments/', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Grievance #{self.id} - {self.guest.username} - {self.problem_type}"

class MaintenanceWork(models.Model):
    STATUS_CHOICES = [
        ('ASSIGNED', 'Assigned'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
    ]
    
    grievance = models.OneToOneField(Grievance, on_delete=models.CASCADE)
    assigned_worker = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
                                       limit_choices_to={'role': 'MAINTENANCE'}, related_name='admin_assigned_work')  # Added related_name
    supervisor_name = models.CharField(max_length=100)
    supervisor_phone = models.CharField(max_length=15)
    worker_name = models.CharField(max_length=100)
    worker_phone = models.CharField(max_length=15)
    parts_replaced_fixed = models.TextField()
    product_replaced = models.CharField(max_length=200, blank=True)
    product_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    labour_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    bill_invoice_pic = models.ImageField(upload_to='maintenance_bills/', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ASSIGNED')
    assigned_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Maintenance Work #{self.id} - Grievance #{self.grievance.id}"
    
    def save(self, *args, **kwargs):
        if self.status == 'COMPLETED' and not self.completed_at:
            self.completed_at = timezone.now()
            # Update related grievance status
            self.grievance.status = 'COMPLETED'
            self.grievance.save()
        super().save(*args, **kwargs)

class WorkerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'role': 'MAINTENANCE'})
    employee_id = models.CharField(max_length=20, unique=True)
    specialization = models.CharField(max_length=100)  # e.g., Plumbing, Electrical, etc.
    experience_years = models.IntegerField(default=0)
    is_available = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.specialization}"