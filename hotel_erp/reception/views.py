from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, timedelta
import json

from .models import CustomUser, Room, Booking, Grievance, MaintenanceRecord
from .forms import BookingForm, LoginForm

# Login View
def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                
                # Redirect based on user type - with safe attribute access
                user_type = getattr(user, 'user_type', None)
                if user_type == 'reception':
                    return redirect('reception_dashboard')
                elif user_type == 'guest':
                    return redirect('guest_dashboard')
                elif user_type == 'maintenance':
                    return redirect('maintenance_dashboard')
                elif user_type == 'admin':
                    return redirect('admin_dashboard')
                else:
                    return redirect('home')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    
    return render(request, 'reception/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

# Reception Dashboard
@login_required
def reception_dashboard(request):
    # Safe attribute access with default fallback
    user_type = getattr(request.user, 'user_type', None)
    if user_type != 'reception':
        messages.error(request, 'Access denied.')
        return redirect('login')
    
    # Get today's statistics
    today = timezone.now().date()
    check_ins_today = Booking.objects.filter(check_in_date=today).count()
    check_outs_today = Booking.objects.filter(check_out_date=today).count()
    total_rooms = Room.objects.count()
    available_rooms = Room.objects.filter(is_available=True).count()
    
    context = {
        'check_ins_today': check_ins_today,
        'check_outs_today': check_outs_today,
        'total_rooms': total_rooms,
        'available_rooms': available_rooms,
        'occupied_rooms': total_rooms - available_rooms,
    }
    
    return render(request, 'reception/dashboard.html', context)

# Room Booking
@login_required
def create_booking(request):
    user_type = getattr(request.user, 'user_type', None)
    if user_type != 'reception':
        messages.error(request, 'Access denied.')
        return redirect('login')
    
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.created_by = request.user
            
            # Calculate total amount
            nights = (booking.check_out_date - booking.check_in_date).days
            booking.total_amount = booking.room.price_per_night * nights
            
            # Check room availability
            conflicting_bookings = Booking.objects.filter(
                room=booking.room,
                status__in=['confirmed', 'checked_in'],
                check_in_date__lt=booking.check_out_date,
                check_out_date__gt=booking.check_in_date
            )
            
            if conflicting_bookings.exists():
                messages.error(request, 'Room is not available for the selected dates.')
                return render(request, 'reception/create_booking.html', {'form': form, 'rooms': Room.objects.all()})
            
            booking.save()
            
            # Create temporary guest user
            guest_username = booking.guest_email
            guest_password = booking.guest_phone
            
            # Check if user already exists
            try:
                guest_user = CustomUser.objects.get(username=guest_username)
                guest_user.is_active = True
                guest_user.save()
            except CustomUser.DoesNotExist:
                guest_user = CustomUser.objects.create_user(
                    username=guest_username,
                    email=booking.guest_email,
                    password=guest_password,
                    phone_number=booking.guest_phone,
                    first_name=booking.guest_name.split()[0],
                    last_name=' '.join(booking.guest_name.split()[1:]) if len(booking.guest_name.split()) > 1 else ''
                )
                # Set user_type and is_temporary if your model supports it
                if hasattr(guest_user, 'user_type'):
                    guest_user.user_type = 'guest'
                if hasattr(guest_user, 'is_temporary'):
                    guest_user.is_temporary = True
                guest_user.save()
            
            booking.guest_user = guest_user
            booking.save()
            
            # Mark room as unavailable
            booking.room.is_available = False
            booking.room.save()
            
            messages.success(request, f'Booking created successfully! Booking ID: {booking.booking_id}')
            messages.info(request, f'Guest login credentials - Username: {guest_username}, Password: {guest_password}')
            
            return redirect('reception_dashboard')
    else:
        form = BookingForm()
    
    rooms = Room.objects.filter(is_available=True)
    return render(request, 'reception/create_booking.html', {'form': form, 'rooms': rooms})

# View All Bookings
@login_required
def view_bookings(request):
    user_type = getattr(request.user, 'user_type', None)
    if user_type != 'reception':
        messages.error(request, 'Access denied.')
        return redirect('login')
    
    bookings = Booking.objects.all().order_by('-created_at')
    return render(request, 'reception/view_bookings.html', {'bookings': bookings})

# Check-in Process
@login_required
def check_in(request, booking_id):
    user_type = getattr(request.user, 'user_type', None)
    if user_type != 'reception':
        messages.error(request, 'Access denied.')
        return redirect('login')
    
    booking = get_object_or_404(Booking, booking_id=booking_id)
    
    if booking.status == 'confirmed':
        booking.status = 'checked_in'
        booking.save()
        messages.success(request, f'Guest {booking.guest_name} checked in successfully.')
    else:
        messages.error(request, 'Invalid booking status for check-in.')
    
    return redirect('view_bookings')

# Check-out Process
@login_required
def check_out(request, booking_id):
    user_type = getattr(request.user, 'user_type', None)
    if user_type != 'reception':
        messages.error(request, 'Access denied.')
        return redirect('login')
    
    booking = get_object_or_404(Booking, booking_id=booking_id)
    
    if booking.status == 'checked_in':
        booking.status = 'checked_out'
        booking.save()
        
        # Make room available again
        booking.room.is_available = True
        booking.room.save()
        
        # Deactivate guest user
        if booking.guest_user:
            booking.guest_user.is_active = False
            booking.guest_user.save()
        
        messages.success(request, f'Guest {booking.guest_name} checked out successfully.')
    else:
        messages.error(request, 'Invalid booking status for check-out.')
    
    return redirect('view_bookings')

# AJAX view to get room details
@csrf_exempt
def get_room_details(request):
    if request.method == 'POST':
        room_id = request.POST.get('room_id')
        room = get_object_or_404(Room, id=room_id)
        
        data = {
            'room_number': room.room_number,
            'room_type': room.room_type,
            'price_per_night': str(room.price_per_night),
            'max_occupancy': room.max_occupancy,
            'amenities': room.amenities,
        }
        
        return JsonResponse(data)
    
    return JsonResponse({'error': 'Invalid request'})

# Search bookings
@login_required
def search_bookings(request):
    user_type = getattr(request.user, 'user_type', None)
    if user_type != 'reception':
        messages.error(request, 'Access denied.')
        return redirect('login')
    
    query = request.GET.get('q', '')
    bookings = Booking.objects.all()
    
    if query:
        bookings = bookings.filter(
            Q(guest_name__icontains=query) |
            Q(guest_email__icontains=query) |
            Q(guest_phone__icontains=query) |
            Q(booking_id__icontains=query) |
            Q(room__room_number__icontains=query)
        )
    
    bookings = bookings.order_by('-created_at')
    
    return render(request, 'reception/search_bookings.html', {
        'bookings': bookings,
        'query': query
    })