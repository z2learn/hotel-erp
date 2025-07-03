from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from decimal import Decimal

User = get_user_model()

class Grievance(models.Model):
    PROBLEM_TYPES = [
        ('plumbing', 'Plumbing Issues'),
        ('electrical', 'Electrical Problems'),
        ('ac_heating', 'AC/Heating'),
        ('cleaning', 'Cleaning Issues'),
        ('furniture', 'Furniture Problems'),
        ('wifi', 'WiFi/Internet'),
        ('tv', 'TV/Entertainment'),
        ('bathroom', 'Bathroom Issues'),
        ('noise', 'Noise Complaints'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    grievance_id = models.AutoField(primary_key=True)
    guest = models.ForeignKey(User, on_delete=models.CASCADE, related_name='grievances')
    booking_id = models.CharField(max_length=20)  # Reference to booking
    guest_name = models.CharField(max_length=100)
    guest_email = models.EmailField()
    guest_phone = models.CharField(max_length=15)
    room_number = models.CharField(max_length=10)
    problem_type = models.CharField(max_length=20, choices=PROBLEM_TYPES)
    description = models.TextField()
    attachment = models.ImageField(upload_to='grievance_attachments/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=10, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], default='medium')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_grievances')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Grievance #{self.grievance_id} - {self.guest_name} - {self.get_problem_type_display()}"


class MaintenanceWork(models.Model):
    WORK_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold'),
    ]
    
    work_id = models.AutoField(primary_key=True)
    grievance = models.OneToOneField(Grievance, on_delete=models.CASCADE, related_name='maintenance_work')
    supervisor_name = models.CharField(max_length=100)
    supervisor_phone = models.CharField(max_length=15)
    worker_name = models.CharField(max_length=100)
    worker_phone = models.CharField(max_length=15)
    work_description = models.TextField()
    parts_replaced = models.TextField(blank=True)
    product_name = models.CharField(max_length=200, blank=True)
    product_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(Decimal('0.00'))])
    labor_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(Decimal('0.00'))])
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    invoice_image = models.ImageField(upload_to='invoice_images/', blank=True, null=True)
    work_status = models.CharField(max_length=20, choices=WORK_STATUS_CHOICES, default='pending')
    start_time = models.DateTimeField(blank=True, null=True)
    completion_time = models.DateTimeField(blank=True, null=True)
    remarks = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        # Calculate total cost
        self.total_cost = self.product_cost + self.labor_charge
        super().save(*args, **kwargs)
        
        # Update grievance status based on work status
        if self.work_status == 'completed':
            self.grievance.status = 'completed'
            self.grievance.save()
        elif self.work_status == 'in_progress':
            self.grievance.status = 'in_progress'
            self.grievance.save()
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Work #{self.work_id} - {self.grievance.guest_name} - {self.worker_name}"
