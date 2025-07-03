from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = 'authentication'

urlpatterns = [
    # Main login page
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # AJAX endpoints
    path('ajax/login/', views.ajax_login, name='ajax_login'),
    path('ajax/create-guest-login/', views.create_guest_login, name='create_guest_login'),
    
    # Authentication actions
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_redirect, name='dashboard'),
    
    # User profile
    path('profile/', views.profile_view, name='profile'),
    
    # Individual dashboard views - These will render the correct templates
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('reception-dashboard/', views.reception_dashboard, name='reception_dashboard'),  
    path('maintenance-dashboard/', views.maintenance_dashboard, name='maintenance_dashboard'),
    path('guest-dashboard/', views.guest_dashboard, name='guest_dashboard'),
]