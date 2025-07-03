from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Room, Booking, GuestCredentials, Grievance, MaintenanceTicket

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['room_number', 'room_type', 'price_per_night', 'is_available', 'created_at']
    list_filter = ['room_type', 'is_available']
    search_fields = ['room_number', 'room_type']
    list_editable = ['is_available', 'price_per_night']

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['id', 'guest_name', 'guest_email', 'room', 'check_in_date', 'check_out_date', 'booking_status', 'created_at']
    list_filter = ['booking_status', 'check_in_date', 'check_out_date', 'created_at']
    search_fields = ['guest_name', 'guest_email', 'guest_phone', 'room__room_number']
    readonly_fields = ['created_at']
    date_hierarchy = 'check_in_date'
    
    fieldsets = (
        ('Guest Information', {
            'fields': ('guest_name', 'guest_email', 'guest_phone')
        }),
        ('Booking Details', {
            'fields': ('room', 'check_in_date', 'check_out_date', 'number_of_guests', 'total_amount')
        }),
        ('Status & Additional Info', {
            'fields': ('booking_status', 'special_requests', 'created_by', 'created_at')
        })
    )

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new booking
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(GuestCredentials)
class GuestCredentialsAdmin(admin.ModelAdmin):
    list_display = ['username', 'booking_guest_name', 'booking_room', 'is_active', 'expires_at', 'created_at']
    list_filter = ['is_active', 'expires_at', 'created_at']
    search_fields = ['username', 'booking__guest_name', 'booking__room__room_number']
    readonly_fields = ['created_at']
    
    def booking_guest_name(self, obj):
        return obj.booking.guest_name
    booking_guest_name.short_description = 'Guest Name'
    
    def booking_room(self, obj):
        return obj.booking.room.room_number
    booking_room.short_description = 'Room'

@admin.register(Grievance)
class GrievanceAdmin(admin.ModelAdmin):
    list_display = ['id', 'guest_name', 'room_number', 'problem_type', 'status', 'priority', 'created_at', 'attachment_preview']
    list_filter = ['status', 'priority', 'problem_type', 'created_at']
    search_fields = ['booking__guest_name', 'booking__room__room_number', 'problem_description']
    readonly_fields = ['created_at', 'updated_at', 'attachment_preview']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Grievance Information', {
            'fields': ('booking', 'problem_type', 'problem_description')
        }),
        ('Status & Priority', {
            'fields': ('status', 'priority')
        }),
        ('Attachment', {
            'fields': ('attachment', 'attachment_preview')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'resolved_at'),
            'classes': ('collapse',)
        })
    )
    
    def guest_name(self, obj):
        return obj.booking.guest_name
    guest_name.short_description = 'Guest Name'
    
    def room_number(self, obj):
        return obj.booking.room.room_number
    room_number.short_description = 'Room'
    
    def attachment_preview(self, obj):
        if obj.attachment:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px;" />',
                obj.attachment.url
            )
        return "No attachment"
    attachment_preview.short_description = 'Attachment Preview'

@admin.register(MaintenanceTicket)
class MaintenanceTicketAdmin(admin.ModelAdmin):
    list_display = ['id', 'grievance_id', 'guest_name', 'worker_name', 'supervisor_name', 'total_cost', 'work_completed_at']
    list_filter = ['work_completed_at', 'created_by']
    search_fields = ['grievance__booking__guest_name', 'worker_name', 'supervisor_name']
    readonly_fields = ['work_completed_at', 'bill_preview']
    
    fieldsets = (
        ('Related Grievance', {
            'fields': ('grievance',)
        }),
        ('Supervisor Information', {
            'fields': ('supervisor_name', 'supervisor_phone')
        }),
        ('Worker Information', {
            'fields': ('worker_name', 'worker_phone')
        }),
        ('Work Details', {
            'fields': ('parts_replaced_fixed', 'product_replaced', 'product_cost', 'labour_charge')
        }),
        ('Documentation', {
            'fields': ('bill_invoice', 'bill_preview')
        }),
        ('System Information', {
            'fields': ('created_by', 'work_completed_at'),
            'classes': ('collapse',)
        })
    )
    
    def guest_name(self, obj):
        return obj.grievance.booking.guest_name
    guest_name.short_description = 'Guest Name'
    
    def grievance_id(self, obj):
        return f"#{obj.grievance.id}"
    grievance_id.short_description = 'Grievance ID'
    
    def total_cost(self, obj):
        return f"${obj.product_cost + obj.labour_charge}"
    total_cost.short_description = 'Total Cost'
    
    def bill_preview(self, obj):
        if obj.bill_invoice:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px;" />',
                obj.bill_invoice.url
            )
        return "No bill uploaded"
    bill_preview.short_description = 'Bill Preview'
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new maintenance ticket
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

# Custom admin site configuration
admin.site.site_header = "Hotel Management System"
admin.site.site_title = "Hotel Admin"
admin.site.index_title = "Hotel Management Dashboard"