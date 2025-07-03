from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import logout
from django.contrib import messages
from .models import CustomUser

class GuestSessionMiddleware:
    """Middleware to handle guest session expiration"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if user is authenticated and is a guest
        if (request.user.is_authenticated and 
            request.user.role == 'guest' and 
            request.user.is_temporary):
            
            # Check if guest session has expired
            if request.user.is_expired():
                logout(request)
                messages.warning(request, 'Your guest session has expired.')
                return redirect('authentication:login')
        
        response = self.get_response(request)
        return response

class RoleBasedAccessMiddleware:
    """Middleware to enforce role-based access control"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Define role-based URL patterns - Updated for authentication app structure
        self.role_patterns = {
            'admin': ['/authentication/admin-dashboard/', '/admin/'],
            'reception': ['/authentication/reception-dashboard/', '/reception/'],
            'maintenance': ['/authentication/maintenance-dashboard/', '/maintenance/'],
            'guest': ['/authentication/guest-dashboard/', '/guest/']
        }
        
        # Public URLs that don't require authentication
        self.public_urls = [
            '/',
            '/authentication/',
            '/authentication/login/',
            '/authentication/ajax/',
            '/static/',
            '/media/',
            '/admin/login/',
        ]

    def __call__(self, request):
        # Skip middleware for public URLs
        if any(request.path.startswith(url) for url in self.public_urls):
            response = self.get_response(request)
            return response
        
        # Skip middleware for unauthenticated users
        if not request.user.is_authenticated:
            response = self.get_response(request)
            return response
        
        # Check role-based access
        user_role = request.user.role
        current_path = request.path
        
        # Check if user is trying to access a restricted area
        for role, patterns in self.role_patterns.items():
            if any(current_path.startswith(pattern) for pattern in patterns):
                # Allow admin access to all areas, or matching role access
                if user_role != role and user_role != 'admin':
                    # Redirect to appropriate dashboard
                    dashboard_url = self.get_dashboard_url(user_role)
                    messages.error(request, 'Access denied. You do not have permission to access this page.')
                    return redirect(dashboard_url)
                break
        
        response = self.get_response(request)
        return response
    
    def get_dashboard_url(self, role):
        """Get dashboard URL based on user role"""
        role_urls = {
            'admin': '/authentication/admin-dashboard/',
            'reception': '/authentication/reception-dashboard/',
            'maintenance': '/authentication/maintenance-dashboard/',
            'guest': '/authentication/guest-dashboard/'
        }
        return role_urls.get(role, '/authentication/login/')

class LoginAttemptMiddleware:
    """Middleware to track and limit login attempts"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.max_attempts = 5
        self.lockout_duration = 300  # 5 minutes in seconds

    def __call__(self, request):
        response = self.get_response(request)
        return response
    
    def is_locked_out(self, ip_address):
        """Check if IP is locked out due to too many failed attempts"""
        from .models import LoginAttempt
        from datetime import timedelta
        
        cutoff_time = timezone.now() - timedelta(seconds=self.lockout_duration)
        recent_attempts = LoginAttempt.objects.filter(
            ip_address=ip_address,
            attempted_at__gte=cutoff_time,
            success=False
        ).count()
        
        return recent_attempts >= self.max_attempts

class SessionSecurityMiddleware:
    """Middleware to enhance session security"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Check for session hijacking by comparing user agent
            stored_user_agent = request.session.get('user_agent')
            current_user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            if stored_user_agent and stored_user_agent != current_user_agent:
                # Potential session hijacking detected
                logout(request)
                messages.error(request, 'Session security violation detected. Please login again.')
                return redirect('authentication:login')
            
            # Store user agent in session if not already stored
            if not stored_user_agent:
                request.session['user_agent'] = current_user_agent
        
        response = self.get_response(request)
        return response