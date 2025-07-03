from django.urls import path
from . import views

app_name = 'reception'

urlpatterns = [
    # Dashboard - Main entry point
    path('', views.reception_dashboard, name='dashboard'),
    path('dashboard/', views.reception_dashboard, name='dashboard'),
    
    # Booking Management
    path('booking/create/', views.create_booking, name='create_booking'),
    path('bookings/', views.view_bookings, name='view_bookings'),
    path('bookings/search/', views.search_bookings, name='search_bookings'),
    path('checkin/<uuid:booking_id>/', views.check_in, name='check_in'),
    path('checkout/<uuid:booking_id>/', views.check_out, name='check_out'),
    
    # AJAX endpoints
    path('api/room-details/', views.get_room_details, name='get_room_details'),
]