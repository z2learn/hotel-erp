from django.urls import path
from . import views

app_name = 'guest'

urlpatterns = [
    # Dashboard - Main entry point
    path('', views.guest_dashboard, name='dashboard'),
    path('dashboard/', views.guest_dashboard, name='dashboard'),
    
    # Legacy support
    path('home/', views.guest_home, name='home'),
    path('guest_home/', views.guest_home, name='guest_home'),
    
    # Grievance Management
    path('grievance/create/', views.create_grievance, name='create_grievance'),
    path('grievance/<int:grievance_id>/', views.grievance_detail, name='grievance_detail'),
    path('api/grievance-status/', views.check_grievance_status, name='check_grievance_status'),
]