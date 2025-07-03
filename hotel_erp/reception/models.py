from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
import uuid

class CustomUser(AbstractUser):
    USER_TYPES = (
        ('admin', 'Admin'),
        ('reception', 'Reception'),
        ('guest', 'Guest'),
        ('maintenance', 'Maintenance'),
    )
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='guest')
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    is_temporary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class Room(models.Model):
    ROOM_TYPES = (
        ('single', 'Single'),
        ('double', 'Double'),
        ('suite', 'Suite'),
        ('deluxe', 'Deluxe'),
        ('family', 'Family'),
    )
    room_number = models.CharField(max_length=10, unique=True)
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES)
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)
    is_available = models.BooleanField(default=True)
    max_occupancy = models.IntegerField(default=2)
    amenities = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Room {self.room_number} - {self.room_type}"

class Booking(models.Model):
    BOOKING_STATUS = (
        ('confirmed', 'Confirmed'),
        ('checked_in', 'Checked In'),
        ('checked_out', 'Checked Out'),
        ('cancelled', 'Cancelled'),
    )
    booking_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    guest_name = models.CharField(max_length=100)
    guest_email = models.EmailField()
    guest_phone = models.CharField(max_length=17)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    number_of_guests = models.IntegerField(default=1)
    special_requests = models.TextField(blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    advance_payment = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=BOOKING_STATUS, default='confirmed')
    guest_user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='bookings_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Booking {self.booking_id} - {self.guest_name}"

    def calculate_total_nights(self):
        return (self.check_out_date - self.check_in_date).days

    def calculate_total_amount(self):
        nights = self.calculate_total_nights()
        return self.room.price_per_night * nights

class Grievance(models.Model):
    PROBLEM_TYPES = (
        ('room_cleaning', 'Room Cleaning'),
        ('ac_heating', 'AC/Heating'),
        ('plumbing', 'Plumbing'),
        ('electrical', 'Electrical'),
        ('wifi_tv', 'WiFi/TV'),
        ('noise', 'Noise Complaint'),
        ('room_service', 'Room Service'),
        ('front_desk', 'Front Desk'),
        ('others', 'Others'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    )
    
    grievance_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    guest = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)
    problem_type = models.CharField(max_length=20, choices=PROBLEM_TYPES)
    problem_description = models.TextField()
    attachment = models.ImageField(upload_to='grievance_attachments/', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Grievance {self.grievance_id} - {self.problem_type}"

class MaintenanceRecord(models.Model):
    grievance = models.OneToOneField(Grievance, on_delete=models.CASCADE)
    supervisor_name = models.CharField(max_length=100)
    supervisor_phone = models.CharField(max_length=17)
    worker_name = models.CharField(max_length=100)
    worker_phone = models.CharField(max_length=17)
    parts_replaced_fixed = models.TextField()
    product_replaced = models.CharField(max_length=200, blank=True)
    product_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    labour_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    bill_invoice = models.ImageField(upload_to='maintenance_bills/', null=True, blank=True)
    completed_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)

    def __str__(self):
        return f"Maintenance for {self.grievance.grievance_id}"
class MaintenanceTicket(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    issue_description = models.TextField()
    priority = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ])
    status = models.CharField(max_length=20, choices=[
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('closed', 'Closed')
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Ticket #{self.id} - {self.room}"