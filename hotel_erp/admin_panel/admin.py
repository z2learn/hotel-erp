from django.contrib import admin
from django.utils.html import format_html
from .models import Room, Booking, Grievance, MaintenanceWork, WorkerProfile

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['room_number', 'room_type', 'price_per_night', 'is_available', 'max_occupancy']
    list_filter = ['room_type', 'is_available']
    search_fields = ['room_number', 'room_type']
    list_editable = ['is_available', 'price_per_night']

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    # Removed 'status' from list_display and list_filter since it doesn't exist in the model
    list_display = ['id', 'guest_name', 'guest_email', 'room', 'check_in_date', 'check_out_date', 'total_amount', 'created_at']
    list_filter = ['check_in_date', 'check_out_date', 'created_at']
    search_fields = ['guest_name', 'guest_email', 'guest_phone', 'room__room_number']
    readonly_fields = ['created_at', 'total_amount']
    date_hierarchy = 'check_in_date'
    
    fieldsets = (
        ('Guest Information', {
            'fields': ('guest_name', 'guest_email', 'guest_phone')
        }),
        ('Booking Details', {
            'fields': ('room', 'check_in_date', 'check_out_date', 'number_of_guests', 'total_amount')
        }),
        ('Additional Info', {
            'fields': ('special_requests', 'created_by', 'guest_user', 'created_at')
        })
    )

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new booking
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(Grievance)
class GrievanceAdmin(admin.ModelAdmin):
    list_display = ['id', 'guest_username', 'booking_room', 'problem_type', 'status', 'created_at', 'attachment_preview']
    list_filter = ['status', 'problem_type', 'created_at']
    search_fields = ['guest__username', 'booking__room__room_number', 'detailed_description']
    readonly_fields = ['created_at', 'updated_at', 'attachment_preview']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Grievance Information', {
            'fields': ('guest', 'booking', 'problem_type', 'detailed_description')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Attachment', {
            'fields': ('attachment', 'attachment_preview')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def guest_username(self, obj):
        return obj.guest.username
    guest_username.short_description = 'Guest'
    
    def booking_room(self, obj):
        return obj.booking.room.room_number
    booking_room.short_description = 'Room'
    
    def attachment_preview(self, obj):
        if obj.attachment:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px;" />',
                obj.attachment.url
            )
        return "No attachment"
    attachment_preview.short_description = 'Attachment Preview'

@admin.register(MaintenanceWork)
class MaintenanceWorkAdmin(admin.ModelAdmin):
    list_display = ['id', 'grievance_id', 'worker_username', 'supervisor_name', 'status', 'total_cost', 'assigned_at', 'completed_at']
    list_filter = ['status', 'assigned_at', 'completed_at']
    search_fields = ['grievance__guest__username', 'assigned_worker__username', 'supervisor_name', 'worker_name']
    readonly_fields = ['assigned_at', 'completed_at', 'bill_preview', 'total_cost']
    
    fieldsets = (
        ('Related Grievance', {
            'fields': ('grievance',)
        }),
        ('Assignment', {
            'fields': ('assigned_worker', 'status')
        }),
        ('Supervisor Information', {
            'fields': ('supervisor_name', 'supervisor_phone')
        }),
        ('Worker Information', {
            'fields': ('worker_name', 'worker_phone')
        }),
        ('Work Details', {
            'fields': ('parts_replaced_fixed', 'product_replaced', 'product_cost', 'labour_charge', 'total_cost')
        }),
        ('Documentation', {
            'fields': ('bill_invoice_pic', 'bill_preview')
        }),
        ('Timestamps', {
            'fields': ('assigned_at', 'completed_at'),
            'classes': ('collapse',)
        })
    )
    
    def worker_username(self, obj):
        return obj.assigned_worker.username
    worker_username.short_description = 'Assigned Worker'
    
    def grievance_id(self, obj):
        return f"#{obj.grievance.id}"
    grievance_id.short_description = 'Grievance ID'
    
    def total_cost(self, obj):
        return f"${obj.product_cost + obj.labour_charge}"
    total_cost.short_description = 'Total Cost'
    
    def bill_preview(self, obj):
        if obj.bill_invoice_pic:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px;" />',
                obj.bill_invoice_pic.url
            )
        return "No bill uploaded"
    bill_preview.short_description = 'Bill Preview'

@admin.register(WorkerProfile)
class WorkerProfileAdmin(admin.ModelAdmin):
    list_display = ['user_username', 'employee_id', 'specialization', 'experience_years', 'is_available']
    list_filter = ['specialization', 'is_available', 'experience_years']
    search_fields = ['user__username', 'employee_id', 'specialization']
    list_editable = ['is_available']
    
    def user_username(self, obj):
        return obj.user.username
    user_username.short_description = 'Username'