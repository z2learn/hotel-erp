from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Room, Booking, Grievance, MaintenanceTicket

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['room_number', 'room_type', 'price_per_night', 'is_available', 'created_at']
    list_filter = ['room_type', 'is_available']
    search_fields = ['room_number', 'room_type']
    list_editable = ['is_available', 'price_per_night']

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['id', 'guest_name', 'guest_email', 'room', 'check_in_date', 'check_out_date', 'status', 'created_at']
    list_filter = ['status', 'check_in_date', 'check_out_date', 'created_at']
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
            'fields': ('status', 'special_requests', 'created_by', 'created_at')
        })
    )

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new booking
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(Grievance)
class GrievanceAdmin(admin.ModelAdmin):
    list_display = ['id', 'guest_name', 'room_number', 'problem_type', 'status', 'created_at', 'attachment_preview']
    list_filter = ['status', 'problem_type', 'created_at']
    search_fields = ['booking__guest_name', 'booking__room__room_number', 'problem_description']
    readonly_fields = ['created_at', 'updated_at', 'attachment_preview']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Grievance Information', {
            'fields': ('booking', 'problem_type', 'problem_description')
        }),
        ('Status', {
            'fields': ('status',)
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
        return obj.booking.guest_name if obj.booking else 'No booking'
    guest_name.short_description = 'Guest Name'
    
    def room_number(self, obj):
        return obj.booking.room.room_number if obj.booking and obj.booking.room else 'No room'
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
    # Basic safe configuration - only using common fields
    list_display = ['id', 'created_at']
    list_filter = ['created_at']
    readonly_fields = ['created_at']
    
    # Minimal fieldsets - add more fields as needed based on your actual model
    fieldsets = (
        ('Basic Information', {
            'fields': ('created_at',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new maintenance ticket
            if hasattr(obj, 'created_by'):
                obj.created_by = request.user
        super().save_model(request, obj, form, change)

# Custom admin site configuration
admin.site.site_header = "Hotel Management System"
admin.site.site_title = "Hotel Admin"
admin.site.index_title = "Hotel Management Dashboard"