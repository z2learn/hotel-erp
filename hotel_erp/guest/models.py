# guest/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone

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
    created_at = models.DateTimeField(auto_now_add=True)  # Added missing field
    
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
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='guest_bookings')  # Added related_name
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Booking #{self.id} - {self.guest_name} - Room {self.room.room_number}"

class GuestCredentials(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE)
    username = models.CharField(max_length=150)  # Added missing field
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='guest_credentials')
    temporary_password = models.CharField(max_length=20)
    is_active = models.BooleanField(default=False)  # Renamed from 'is_activated'
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()  # Renamed from 'valid_until'
    
    def __str__(self):
        return f"Credentials for {self.booking.guest_name}"

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
    
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]
    
    guest = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
                             limit_choices_to={'role': 'GUEST'}, related_name='guest_grievances')  # Added related_name
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)
    problem_type = models.CharField(max_length=50, choices=PROBLEM_TYPES)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')  # Added missing field
    detailed_description = models.TextField()
    attachment = models.ImageField(upload_to='grievance_attachments/', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Grievance #{self.id} - {self.guest.username} - {self.problem_type}"

class MaintenanceTicket(models.Model):
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('ASSIGNED', 'Assigned'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CLOSED', 'Closed'),
    ]
    
    grievance = models.OneToOneField(Grievance, on_delete=models.CASCADE)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='guest_maintenance_tickets')  # Added related_name
    assigned_worker = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        limit_choices_to={'role': 'MAINTENANCE'},
        related_name='guest_assigned_tickets'  # Added related_name
    )
    worker_name = models.CharField(max_length=100, blank=True)  # Added missing field
    supervisor_name = models.CharField(max_length=100, blank=True)  # Added missing field
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    actual_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    bill_invoice = models.ImageField(upload_to='maintenance_bills/', null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    work_completed_at = models.DateTimeField(null=True, blank=True)  # Added missing field
    
    def __str__(self):
        return f"Ticket #{self.id} - {self.grievance.problem_type}"
    
    def save(self, *args, **kwargs):
        if self.status == 'COMPLETED' and not self.completed_at:
            self.completed_at = timezone.now()
            self.work_completed_at = timezone.now()
            # Update related grievance status
            self.grievance.status = 'COMPLETED'
            self.grievance.save()
        super().save(*args, **kwargs)