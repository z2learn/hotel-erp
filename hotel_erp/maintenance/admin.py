# admin.py
from django.contrib import admin
from .models import Grievance, MaintenanceWork

@admin.register(Grievance)
class GrievanceAdmin(admin.ModelAdmin):
    list_display = ['grievance_id', 'guest_name', 'room_number', 'problem_type', 'status', 'priority', 'assigned_to', 'created_at']
    list_filter = ['status', 'priority', 'problem_type', 'created_at']
    search_fields = ['guest_name', 'guest_email', 'room_number', 'description']
    readonly_fields = ['grievance_id', 'created_at', 'updated_at']
    list_per_page = 25
    
    fieldsets = (
        ('Grievance Information', {
            'fields': ('grievance_id', 'guest', 'booking_id', 'guest_name', 'guest_email', 'guest_phone', 'room_number')
        }),
        ('Problem Details', {
            'fields': ('problem_type', 'description', 'attachment')
        }),
        ('Status & Assignment', {
            'fields': ('status', 'priority', 'assigned_to')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(MaintenanceWork)
class MaintenanceWorkAdmin(admin.ModelAdmin):
    list_display = ['work_id', 'grievance', 'worker_name', 'work_status', 'total_cost', 'created_at']
    list_filter = ['work_status', 'created_at']
    search_fields = ['worker_name', 'supervisor_name', 'grievance__guest_name']
    readonly_fields = ['work_id', 'total_cost', 'created_at', 'updated_at']
    list_per_page = 25
    
    fieldsets = (
        ('Work Information', {
            'fields': ('work_id', 'grievance', 'work_status')
        }),
        ('Staff Details', {
            'fields': ('supervisor_name', 'supervisor_phone', 'worker_name', 'worker_phone')
        }),
        ('Work Details', {
            'fields': ('work_description', 'parts_replaced', 'start_time', 'completion_time')
        }),
        ('Cost Information', {
            'fields': ('product_name', 'product_cost', 'labor_charge', 'total_cost', 'invoice_image')
        }),
        ('Additional Information', {
            'fields': ('remarks', 'created_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )