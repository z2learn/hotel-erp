from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Q, Count

# Fixed imports - import from the correct apps
from authentication.models import CustomUser  # Import CustomUser from authentication app
from reception.models import Room, Booking, Grievance  # Import these from reception app

# Import maintenance models from maintenance app (or comment out if they don't exist)
try:
    from maintenance.models import MaintenanceWork, WorkerProfile
except ImportError:
    # If these don't exist yet, we'll handle it gracefully
    MaintenanceWork = None
    WorkerProfile = None

# Import forms (make sure these exist in admin_panel/forms.py)
try:
    from .forms import WorkerCreationForm, RoomForm, UserProfileForm
except ImportError:
    # Comment out if forms don't exist yet
    WorkerCreationForm = None
    RoomForm = None
    UserProfileForm = None

import json

def is_admin(user):
    return user.is_authenticated and user.role == 'ADMIN'

def login_view(request):
    """Universal login page that redirects based on user role"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Check if guest account is still valid
            if user.role == 'GUEST' and hasattr(user, 'is_temporary') and user.is_temporary:
                if hasattr(user, 'valid_until') and user.valid_until and timezone.now() > user.valid_until:
                    messages.error(request, 'Your guest account has expired.')
                    return render(request, 'admin_panel/login.html')
            
            login(request, user)
            
            # Role-based redirection
            if user.role == 'ADMIN':
                return redirect('admin_panel:dashboard')
            elif user.role == 'RECEPTION':
                return redirect('reception:booking_page')
            elif user.role == 'GUEST':
                return redirect('guest:dashboard')
            elif user.role == 'MAINTENANCE':
                return redirect('maintenance:dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'admin_panel/login.html')

def logout_view(request):
    logout(request)
    return redirect('admin_panel:login')

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    """Admin dashboard with system overview"""
    context = {
        'total_bookings': Booking.objects.count(),
        'active_bookings': Booking.objects.filter(status='CONFIRMED').count(),  # Changed from 'ACTIVE' to 'CONFIRMED'
        'total_rooms': Room.objects.count(),
        'available_rooms': Room.objects.filter(is_available=True).count(),
        'pending_grievances': Grievance.objects.filter(status='PENDING').count(),
        'total_workers': CustomUser.objects.filter(role='MAINTENANCE').count(),
        'recent_bookings': Booking.objects.order_by('-created_at')[:5],
        'recent_grievances': Grievance.objects.order_by('-created_at')[:5],
    }
    return render(request, 'admin_panel/dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def manage_workers(request):
    """Manage maintenance workers"""
    if WorkerProfile is None:
        messages.error(request, 'Worker management is not available yet.')
        return redirect('admin_panel:dashboard')
    
    workers = CustomUser.objects.filter(role='MAINTENANCE').select_related('workerprofile')
    
    if request.method == 'POST' and WorkerCreationForm:
        form = WorkerCreationForm(request.POST)
        if form.is_valid():
            worker = form.save(commit=False)
            worker.role = 'MAINTENANCE'
            worker.save()
            
            # Create worker profile
            WorkerProfile.objects.create(
                user=worker,
                employee_id=form.cleaned_data['employee_id'],
                department=form.cleaned_data.get('department', 'Maintenance'),
            )
            
            messages.success(request, f'Worker {worker.username} created successfully.')
            return redirect('admin_panel:manage_workers')
    else:
        form = WorkerCreationForm() if WorkerCreationForm else None
    
    context = {
        'workers': workers,
        'form': form,
    }
    return render(request, 'admin_panel/manage_workers.html', context)

@login_required
@user_passes_test(is_admin)
def manage_rooms(request):
    """Manage hotel rooms"""
    rooms = Room.objects.all().order_by('room_number')
    
    if request.method == 'POST' and RoomForm:
        form = RoomForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Room added successfully.')
            return redirect('admin_panel:manage_rooms')
    else:
        form = RoomForm() if RoomForm else None
    
    context = {
        'rooms': rooms,
        'form': form,
    }
    return render(request, 'admin_panel/manage_rooms.html', context)

@login_required
@user_passes_test(is_admin)
def manage_bookings(request):
    """View and manage all bookings"""
    bookings = Booking.objects.all().select_related('room', 'created_by').order_by('-created_at')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        bookings = bookings.filter(status=status_filter)
    
    context = {
        'bookings': bookings,
        'status_filter': status_filter,
    }
    return render(request, 'admin_panel/manage_bookings.html', context)

@login_required
@user_passes_test(is_admin)
def manage_grievances(request):
    """View and manage all grievances"""
    grievances = Grievance.objects.all().select_related('guest', 'booking').order_by('-created_at')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        grievances = grievances.filter(status=status_filter)
    
    context = {
        'grievances': grievances,
        'status_filter': status_filter,
    }
    return render(request, 'admin_panel/manage_grievances.html', context)

@login_required
@user_passes_test(is_admin)
def assign_maintenance(request, grievance_id):
    """Assign maintenance work to a worker"""
    if MaintenanceWork is None:
        messages.error(request, 'Maintenance assignment is not available yet.')
        return redirect('admin_panel:manage_grievances')
    
    grievance = get_object_or_404(Grievance, id=grievance_id)
    workers = CustomUser.objects.filter(role='MAINTENANCE')
    
    if request.method == 'POST':
        worker_id = request.POST.get('worker_id')
        worker = get_object_or_404(CustomUser, id=worker_id, role='MAINTENANCE')
        
        # Create maintenance work assignment
        maintenance_work = MaintenanceWork.objects.create(
            grievance=grievance,
            assigned_worker=worker,
            supervisor_name=request.POST.get('supervisor_name', ''),
            supervisor_phone=request.POST.get('supervisor_phone', ''),
            worker_name=worker.get_full_name() or worker.username,
            worker_phone=getattr(worker, 'phone_number', ''),
            parts_replaced_fixed='',
            status='ASSIGNED'
        )
        
        # Update grievance status
        grievance.status = 'IN_PROGRESS'
        grievance.save()
        
        messages.success(request, f'Maintenance work assigned to {worker.username}.')
        return redirect('admin_panel:manage_grievances')
    
    context = {
        'grievance': grievance,
        'workers': workers,
    }
    return render(request, 'admin_panel/assign_maintenance.html', context)

@login_required
@user_passes_test(is_admin)
def user_management(request):
    """Manage all users in the system"""
    users = CustomUser.objects.all().order_by('-date_joined')
    
    # Filter by role if provided
    role_filter = request.GET.get('role')
    if role_filter:
        users = users.filter(role=role_filter)
    
    context = {
        'users': users,
        'role_filter': role_filter,
        'roles': getattr(CustomUser, 'ROLE_CHOICES', []),
    }
    return render(request, 'admin_panel/user_management.html', context)

@login_required
@user_passes_test(is_admin)
def deactivate_user(request, user_id):
    """Deactivate a user account"""
    user = get_object_or_404(CustomUser, id=user_id)
    
    if request.method == 'POST':
        user.is_active = False
        user.save()
        messages.success(request, f'User {user.username} has been deactivated.')
    
    return redirect('admin_panel:user_management')

@login_required
@user_passes_test(is_admin)
def activate_user(request, user_id):
    """Activate a user account"""
    user = get_object_or_404(CustomUser, id=user_id)
    
    if request.method == 'POST':
        user.is_active = True
        user.save()
        messages.success(request, f'User {user.username} has been activated.')
    
    return redirect('admin_panel:user_management')

@login_required
@user_passes_test(is_admin)
def system_reports(request):
    """Generate system reports and analytics"""
    # Monthly booking statistics
    from datetime import datetime, timedelta
    
    current_month = timezone.now().replace(day=1)
    last_month = (current_month - timedelta(days=1)).replace(day=1)
    
    monthly_bookings = Booking.objects.filter(
        created_at__gte=current_month
    ).count()
    
    monthly_revenue = sum([
        booking.total_amount for booking in Booking.objects.filter(
            created_at__gte=current_month, status='CONFIRMED'  # Changed from 'ACTIVE'
        )
    ])
    
    # Grievance statistics
    grievance_stats = Grievance.objects.values('problem_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Room occupancy
    total_rooms = Room.objects.count()
    occupied_rooms = Booking.objects.filter(
        status='CHECKED_IN',  # Changed from 'ACTIVE'
        check_in_date__lte=timezone.now().date(),
        check_out_date__gte=timezone.now().date()
    ).count()
    
    occupancy_rate = (occupied_rooms / total_rooms * 100) if total_rooms > 0 else 0
    
    context = {
        'monthly_bookings': monthly_bookings,
        'monthly_revenue': monthly_revenue,
        'grievance_stats': grievance_stats,
        'occupancy_rate': round(occupancy_rate, 2),
        'total_rooms': total_rooms,
        'occupied_rooms': occupied_rooms,
    }
    return render(request, 'admin_panel/reports.html', context)

@csrf_exempt
@login_required
@user_passes_test(is_admin)
def api_dashboard_stats(request):
    """API endpoint for dashboard statistics"""
    stats = {
        'total_bookings': Booking.objects.count(),
        'active_bookings': Booking.objects.filter(status='CONFIRMED').count(),  # Changed from 'ACTIVE'
        'pending_grievances': Grievance.objects.filter(status='PENDING').count(),
        'available_rooms': Room.objects.filter(is_available=True).count(),
    }
    return JsonResponse(stats)