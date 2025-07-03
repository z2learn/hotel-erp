from django.urls import path
from . import views

app_name = 'maintenance'

urlpatterns = [
    # Dashboard - Main entry point
    path('', views.maintenance_dashboard, name='dashboard'),
    path('dashboard/', views.maintenance_dashboard, name='dashboard'),
    
    # Grievance Management
    path('grievances/', views.grievance_list, name='grievance_list'),
    path('grievances/<int:grievance_id>/', views.grievance_detail, name='grievance_detail'),
    path('grievances/<int:grievance_id>/assign/', views.assign_grievance, name='assign_grievance'),
    path('grievances/<int:grievance_id>/create-work/', views.create_maintenance_work, name='create_maintenance_work'),
    
    # Work Management
    path('work/<int:work_id>/', views.maintenance_work_detail, name='maintenance_work_detail'),
    path('work/<int:work_id>/edit/', views.edit_maintenance_work, name='edit_maintenance_work'),
    path('work/<int:work_id>/update-status/', views.update_work_status, name='update_work_status'),
    path('my-work/', views.my_work, name='my_work'),
]