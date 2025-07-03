from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils import timezone
from .models import Booking, GuestCredentials, Grievance, MaintenanceTicket
from .forms import GrievanceForm
import json

def guest_login_check(request):
    """Custom authentication for guest using email and phone"""
    if request.method == 'POST':
        username = request.POST.get('username')  # email
        password = request.POST.get('password')  # phone
        
        try:
            guest_cred = GuestCredentials.objects.get(
                username=username,
                password=password,
                is_active=True,
                expires_at__gt=timezone.now()
            )
            
            # Store guest info in session
            request.session['guest_id'] = guest_cred.id
            request.session['booking_id'] = guest_cred.booking.id
            request.session['guest_name'] = guest_cred.booking.guest_name
            request.session['is_guest'] = True
            
            return redirect('guest:guest_dashboard')
            
        except GuestCredentials.DoesNotExist:
            messages.error(request, 'Invalid credentials or session expired.')
            return redirect('guest:guest_login')
    
    return render(request, 'guest/login.html')

def guest_logout(request):
    """Logout guest and clear session"""
    if 'is_guest' in request.session:
        del request.session['guest_id']
        del request.session['booking_id']
        del request.session['guest_name']
        del request.session['is_guest']
    return redirect('authentication:login')  # Redirect to main login instead

def guest_required(view_func):
    """Decorator to check if user is authenticated guest"""
    def wrapper(request, *args, **kwargs):
        if not request.session.get('is_guest'):
            messages.error(request, 'Please login to access guest services.')
            return redirect('authentication:login')  # Changed this line
        
        # Check if session is still valid
        try:
            guest_cred = GuestCredentials.objects.get(
                id=request.session.get('guest_id'),
                is_active=True,
                expires_at__gt=timezone.now()
            )
        except GuestCredentials.DoesNotExist:
            messages.error(request, 'Your session has expired.')
            return redirect('guest:guest_logout')
        
        return view_func(request, *args, **kwargs)
    return wrapper

@guest_required
def guest_dashboard(request):
    """Guest dashboard with booking information"""
    booking_id = request.session.get('booking_id')
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Get grievances for this booking
    grievances = Grievance.objects.filter(booking=booking).order_by('-created_at')
    
    # Get maintenance details for resolved grievances
    resolved_grievances = []
    for grievance in grievances.filter(status='resolved'):
        try:
            maintenance = MaintenanceTicket.objects.get(grievance=grievance)
            resolved_grievances.append({
                'grievance': grievance,
                'maintenance': maintenance
            })
        except MaintenanceTicket.DoesNotExist:
            resolved_grievances.append({
                'grievance': grievance,
                'maintenance': None
            })
    
    context = {
        'booking': booking,
        'grievances': grievances,
        'resolved_grievances': resolved_grievances,
        'guest_name': request.session.get('guest_name'),
    }
    
    return render(request, 'guest/dashboard.html', context)

@guest_required
def create_grievance(request):
    """Create new grievance"""
    booking_id = request.session.get('booking_id')
    booking = get_object_or_404(Booking, id=booking_id)
    
    if request.method == 'POST':
        form = GrievanceForm(request.POST, request.FILES)
        if form.is_valid():
            grievance = form.save(commit=False)
            grievance.booking = booking
            
            # Handle file upload size validation (2MB max)
            if grievance.attachment:
                if grievance.attachment.size > 2 * 1024 * 1024:  # 2MB
                    messages.error(request, 'File size should not exceed 2MB.')
                    return render(request, 'guest/create_grievance.html', {'form': form, 'booking': booking})
            
            grievance.save()
            messages.success(request, 'Your grievance has been submitted successfully.')
            return redirect('guest:guest_dashboard')
    else:
        form = GrievanceForm()
    
    context = {
        'form': form,
        'booking': booking,
        'guest_name': request.session.get('guest_name'),
    }
    
    return render(request, 'guest/create_grievance.html', context)

@guest_required
def grievance_detail(request, grievance_id):
    """View detailed grievance information"""
    booking_id = request.session.get('booking_id')
    booking = get_object_or_404(Booking, id=booking_id)
    grievance = get_object_or_404(Grievance, id=grievance_id, booking=booking)
    
    maintenance_ticket = None
    if grievance.status == 'resolved':
        try:
            maintenance_ticket = MaintenanceTicket.objects.get(grievance=grievance)
        except MaintenanceTicket.DoesNotExist:
            pass
    
    context = {
        'grievance': grievance,
        'maintenance_ticket': maintenance_ticket,
        'booking': booking,
        'guest_name': request.session.get('guest_name'),
    }
    
    return render(request, 'guest/grievance_detail.html', context)

@guest_required
def check_grievance_status(request):
    """AJAX endpoint to check grievance status updates"""
    if request.method == 'GET':
        booking_id = request.session.get('booking_id')
        booking = get_object_or_404(Booking, id=booking_id)
        
        grievances = Grievance.objects.filter(booking=booking).values(
            'id', 'problem_type', 'status', 'priority', 'created_at', 'updated_at'
        )
        
        grievance_list = []
        for grievance in grievances:
            grievance['created_at'] = grievance['created_at'].strftime('%Y-%m-%d %H:%M')
            grievance['updated_at'] = grievance['updated_at'].strftime('%Y-%m-%d %H:%M')
            grievance_list.append(grievance)
        
        return JsonResponse({
            'grievances': grievance_list,
            'status': 'success'
        })
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

def guest_login_page(request):
    """Render guest login page"""
    return render(request, 'guest/login.html')

# Add a new view to handle the root guest URL
def guest_home(request):
    """Redirect guest home to authentication login"""
    return redirect('authentication:login')