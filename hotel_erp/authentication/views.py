from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.urls import reverse, NoReverseMatch
import json
import re
from .models import CustomUser, UserSession, LoginAttempt
from .forms import LoginForm

def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def get_user_agent(request):
    """Get user agent from request"""
    return request.META.get('HTTP_USER_AGENT', '')

def login_view(request):
    """Main login view - serves the login page"""
    if request.user.is_authenticated:
        return redirect(get_dashboard_url(request.user.role))
    
    return render(request, 'authentication/login.html')

@csrf_exempt
@require_http_methods(["POST"])
def ajax_login(request):
    """AJAX login endpoint"""
    try:
        data = json.loads(request.body)
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        login_type = data.get('loginType', 'staff')
        remember_me = data.get('rememberMe', False)
        
        # Get client information
        ip_address = get_client_ip(request)
        user_agent = get_user_agent(request)
        
        # Validate input
        if not username or not password:
            return JsonResponse({
                'success': False,
                'message': 'Username and password are required'
            }, status=400)
        
        # Validate email for guest login
        if login_type == 'guest' and not is_valid_email(username):
            return JsonResponse({
                'success': False,
                'message': 'Please enter a valid email address'
            }, status=400)
        
        # Validate phone for guest login
        if login_type == 'guest' and not is_valid_phone(password):
            return JsonResponse({
                'success': False,
                'message': 'Please enter a valid 10-digit phone number'
            }, status=400)
        
        # Authenticate user
        user = authenticate(request, username=username, password=password)
        
        # Log login attempt
        LoginAttempt.objects.create(
            username=username,
            ip_address=ip_address,
            success=user is not None,
            user_agent=user_agent
        )
        
        if user is not None:
            # Check if user is active
            if not user.is_active:
                return JsonResponse({
                    'success': False,
                    'message': 'Account is deactivated'
                }, status=401)
            
            # Check if temporary user is expired
            if hasattr(user, 'is_temporary') and user.is_temporary and hasattr(user, 'is_expired') and user.is_expired():
                return JsonResponse({
                    'success': False,
                    'message': 'Guest access has expired'
                }, status=401)
            
            # Validate login type against user role
            if login_type == 'guest' and user.role != 'guest':
                return JsonResponse({
                    'success': False,
                    'message': 'Please use staff login for staff accounts'
                }, status=401)
            
            if login_type == 'staff' and user.role == 'guest':
                return JsonResponse({
                    'success': False,
                    'message': 'Please use guest login for guest accounts'
                }, status=401)
            
            # Login user
            login(request, user)
            
            # Create user session record
            UserSession.objects.create(
                user=user,
                session_key=request.session.session_key,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Set session expiry based on remember me
            if remember_me:
                request.session.set_expiry(30 * 24 * 60 * 60)  # 30 days
            else:
                request.session.set_expiry(0)  # Browser session
            
            # Get redirect URL
            redirect_url = get_dashboard_url(user.role)
            
            return JsonResponse({
                'success': True,
                'message': 'Login successful',
                'redirect_url': redirect_url,
                'user': {
                    'username': user.username,
                    'role': user.role,
                    'name': user.get_full_name() or user.username
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Invalid username or password'
            }, status=401)
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'An error occurred during login'
        }, status=500)

@login_required
def logout_view(request):
    """Logout view"""
    # Update user session
    try:
        session = UserSession.objects.get(
            user=request.user,
            session_key=request.session.session_key,
            is_active=True
        )
        session.logout_time = timezone.now()
        session.is_active = False
        session.save()
    except UserSession.DoesNotExist:
        pass
    
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('authentication:login')

def get_dashboard_url(role):
    """Get dashboard URL based on user role"""
    try:
        # Use authentication app's dashboard views directly
        role_urls = {
            'admin': 'authentication:admin_dashboard',
            'reception': 'authentication:reception_dashboard', 
            'maintenance': 'authentication:maintenance_dashboard',
            'guest': 'authentication:guest_dashboard'
        }
        
        if role in role_urls:
            try:
                return reverse(role_urls[role])
            except NoReverseMatch:
                # Fallback to direct URLs if named URLs don't work
                pass
        
        # Fallback to direct URLs
        role_direct_urls = {
            'admin': '/authentication/admin-dashboard/',
            'reception': '/authentication/reception-dashboard/',
            'maintenance': '/authentication/maintenance-dashboard/',
            'guest': '/authentication/guest-dashboard/'
        }
        return role_direct_urls.get(role, '/authentication/login/')
        
    except Exception:
        # Final fallback
        return '/authentication/login/'

def is_valid_email(email):
    """Validate email format"""
    pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
    return re.match(pattern, email) is not None

def is_valid_phone(phone):
    """Validate phone number (10 digits)"""
    pattern = r'^\d{10}$'
    return re.match(pattern, phone) is not None

@login_required
def profile_view(request):
    """User profile view"""
    return render(request, 'authentication/profile.html', {
        'user': request.user
    })

def create_guest_credentials(guest_email, guest_phone, booking_duration_days, created_by_user):
    """Create temporary guest credentials"""
    try:
        with transaction.atomic():
            # Check if guest already exists
            existing_user = CustomUser.objects.filter(email=guest_email).first()
            
            if existing_user and existing_user.role == 'guest':
                # Update existing guest user
                existing_user.phone = guest_phone
                if hasattr(existing_user, 'expires_at'):
                    existing_user.expires_at = timezone.now() + timezone.timedelta(days=booking_duration_days)
                existing_user.is_active = True
                existing_user.save()
                return existing_user
            
            # Create new guest user
            guest_user_data = {
                'username': guest_email,
                'email': guest_email,
                'password': guest_phone,
                'role': 'guest',
            }
            
            # Add optional fields if they exist in your model
            if hasattr(CustomUser, 'phone'):
                guest_user_data['phone'] = guest_phone
            if hasattr(CustomUser, 'is_temporary'):
                guest_user_data['is_temporary'] = True
            if hasattr(CustomUser, 'expires_at'):
                guest_user_data['expires_at'] = timezone.now() + timezone.timedelta(days=booking_duration_days)
            if hasattr(CustomUser, 'created_by'):
                guest_user_data['created_by'] = created_by_user
            
            guest_user = CustomUser.objects.create_user(**guest_user_data)
            
            return guest_user
    
    except Exception as e:
        raise ValidationError(f"Error creating guest credentials: {str(e)}")

@require_http_methods(["POST"])
@login_required
def create_guest_login(request):
    """Create guest login credentials (called by reception)"""
    if not hasattr(request.user, 'role') or request.user.role != 'reception':
        return JsonResponse({
            'success': False,
            'message': 'Unauthorized access'
        }, status=403)
    
    try:
        data = json.loads(request.body)
        guest_email = data.get('guest_email')
        guest_phone = data.get('guest_phone')
        booking_duration = int(data.get('booking_duration', 1))
        
        if not guest_email or not guest_phone:
            return JsonResponse({
                'success': False,
                'message': 'Guest email and phone are required'
            }, status=400)
        
        # Create guest credentials
        guest_user = create_guest_credentials(
            guest_email, 
            guest_phone, 
            booking_duration, 
            request.user
        )
        
        response_data = {
            'success': True,
            'message': 'Guest credentials created successfully',
            'credentials': {
                'username': guest_user.username,
                'password': guest_phone,  # For display purposes only
            }
        }
        
        # Add expires_at if it exists
        if hasattr(guest_user, 'expires_at') and guest_user.expires_at:
            response_data['credentials']['expires_at'] = guest_user.expires_at.isoformat()
        
        return JsonResponse(response_data)
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

@login_required
def dashboard_redirect(request):
    """Redirect to appropriate dashboard based on user role"""
    return redirect(get_dashboard_url(request.user.role))

def custom_403(request, exception):
    return render(request, '403.html', status=403)

def custom_404(request, exception):
    return render(request, '404.html', status=404)

def custom_500(request):
    return render(request, '500.html', status=500)

# Dashboard views for each role - Updated to use correct templates
@login_required
def admin_dashboard(request):
    """Admin dashboard view"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('authentication:login')
    
    # Add any admin-specific context data here
    context = {
        'user': request.user,
        'page_title': 'Admin Dashboard',
        'user_role': 'admin'
    }
    
    return render(request, 'admin_panel/dashboard.html', context)

@login_required
def reception_dashboard(request):
    """Reception dashboard view"""
    if request.user.role != 'reception':
        messages.error(request, 'Access denied. Reception privileges required.')
        return redirect('authentication:login')
    
    # Add any reception-specific context data here
    context = {
        'user': request.user,
        'page_title': 'Reception Dashboard',
        'user_role': 'reception'
    }
    
    return render(request, 'reception/dashboard.html', context)

@login_required
def maintenance_dashboard(request):
    """Maintenance dashboard view"""
    if request.user.role != 'maintenance':
        messages.error(request, 'Access denied. Maintenance privileges required.')
        return redirect('authentication:login')
    
    # Add any maintenance-specific context data here
    context = {
        'user': request.user,
        'page_title': 'Maintenance Dashboard',
        'user_role': 'maintenance'
    }
    
    return render(request, 'maintenance/dashboard.html', context)

@login_required
def guest_dashboard(request):
    """Guest dashboard view"""
    if request.user.role != 'guest':
        messages.error(request, 'Access denied. Guest privileges required.')
        return redirect('authentication:login')
    
    # Add any guest-specific context data here
    context = {
        'user': request.user,
        'page_title': 'Guest Portal',
        'user_role': 'guest'
    }
    
    # Check if guest account is expired
    if hasattr(request.user, 'is_expired') and request.user.is_expired():
        messages.warning(request, 'Your guest access has expired.')
        logout(request)
        return redirect('authentication:login')
    
    return render(request, 'guest/dashboard.html', context)