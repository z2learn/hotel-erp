from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    # Dashboard - This is the main entry point after login
    path('', views.admin_dashboard, name='dashboard'),
    path('dashboard/', views.admin_dashboard, name='dashboard'),
    
    # User Management
    path('users/', views.user_management, name='user_management'),
    path('users/deactivate/<int:user_id>/', views.deactivate_user, name='deactivate_user'),
    path('users/activate/<int:user_id>/', views.activate_user, name='activate_user'),
    
    # Worker Management
    path('workers/', views.manage_workers, name='manage_workers'),
    
    # Room Management
    path('rooms/', views.manage_rooms, name='manage_rooms'),
    
    # Booking Management
    path('bookings/', views.manage_bookings, name='manage_bookings'),
    
    # Grievance Management
    path('grievances/', views.manage_grievances, name='manage_grievances'),
    path('grievances/assign/<int:grievance_id>/', views.assign_maintenance, name='assign_maintenance'),
    
    # Reports
    path('reports/', views.system_reports, name='reports'),
    
    # API Endpoints
    path('api/dashboard-stats/', views.api_dashboard_stats, name='api_dashboard_stats'),
]