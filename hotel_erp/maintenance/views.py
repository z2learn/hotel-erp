# views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from .models import Grievance, MaintenanceWork
from .forms import MaintenanceWorkForm, GrievanceAssignForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
from django.contrib.auth.decorators import user_passes_test

def login_view(request):
    """Login view for maintenance module"""
    if request.user.is_authenticated:
        return redirect('maintenance:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                # Check if user has maintenance or admin privileges
                if hasattr(user, 'user_type') and user.user_type in ['maintenance', 'admin']:
                    login(request, user)
                    messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
                    
                    # Redirect to next page or dashboard
                    next_url = request.GET.get('next', 'maintenance:dashboard')
                    return redirect(next_url)
                else:
                    messages.error(request, 'You do not have permission to access the maintenance system.')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Please provide both username and password.')
    
    return render(request, 'maintenance/login.html')

def logout_view(request):
    """Logout view for maintenance module"""
    if request.user.is_authenticated:
        username = request.user.get_full_name() or request.user.username
        logout(request)
        messages.success(request, f'You have been successfully logged out. Goodbye, {username}!')
    
    return redirect('maintenance:login')

def is_maintenance_staff(user):
    return user.is_authenticated and user.user_type in ['maintenance', 'admin']

@login_required
@user_passes_test(is_maintenance_staff)
def maintenance_dashboard(request):
    """Maintenance dashboard with overview statistics"""
    # Get statistics
    pending_grievances = Grievance.objects.filter(status='pending').count()
    assigned_grievances = Grievance.objects.filter(status='assigned').count()
    in_progress_grievances = Grievance.objects.filter(status='in_progress').count()
    completed_today = MaintenanceWork.objects.filter(
        completion_time__date=timezone.now().date()
    ).count()
    
    # Recent grievances
    recent_grievances = Grievance.objects.filter(
        status__in=['pending', 'assigned', 'in_progress']
    )[:10]
    
    # Work assigned to current user (if maintenance staff)
    my_work = []
    if request.user.user_type == 'maintenance':
        my_work = Grievance.objects.filter(
            assigned_to=request.user,
            status__in=['assigned', 'in_progress']
        )[:5]
    
    context = {
        'pending_grievances': pending_grievances,
        'assigned_grievances': assigned_grievances,
        'in_progress_grievances': in_progress_grievances,
        'completed_today': completed_today,
        'recent_grievances': recent_grievances,
        'my_work': my_work,
    }
    return render(request, 'maintenance/dashboard.html', context)

@login_required
@user_passes_test(is_maintenance_staff)
def grievance_list(request):
    """List all grievances with filtering options"""
    grievances = Grievance.objects.all()
    
    # Filtering
    status_filter = request.GET.get('status')
    priority_filter = request.GET.get('priority')
    problem_type_filter = request.GET.get('problem_type')
    search_query = request.GET.get('search')
    
    if status_filter:
        grievances = grievances.filter(status=status_filter)
    
    if priority_filter:
        grievances = grievances.filter(priority=priority_filter)
    
    if problem_type_filter:
        grievances = grievances.filter(problem_type=problem_type_filter)
    
    if search_query:
        grievances = grievances.filter(
            Q(guest_name__icontains=search_query) |
            Q(room_number__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(grievance_id__icontains=search_query)
        )
    
    # Show only assigned work for maintenance staff
    if request.user.user_type == 'maintenance':
        grievances = grievances.filter(
            Q(assigned_to=request.user) | Q(status='pending')
        )
    
    # Pagination
    paginator = Paginator(grievances, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_choices': Grievance.STATUS_CHOICES,
        'priority_choices': Grievance._meta.get_field('priority').choices,
        'problem_type_choices': Grievance.PROBLEM_TYPES,
        'current_filters': {
            'status': status_filter,
            'priority': priority_filter,
            'problem_type': problem_type_filter,
            'search': search_query,
        }
    }
    return render(request, 'maintenance/grievance_list.html', context)

@login_required
@user_passes_test(is_maintenance_staff)
def grievance_detail(request, grievance_id):
    """View grievance details"""
    grievance = get_object_or_404(Grievance, grievance_id=grievance_id)
    maintenance_work = getattr(grievance, 'maintenance_work', None)
    
    # Check if user can view this grievance
    if request.user.user_type == 'maintenance' and grievance.assigned_to != request.user and grievance.status != 'pending':
        messages.error(request, "You don't have permission to view this grievance.")
        return redirect('maintenance:grievance_list')
    
    context = {
        'grievance': grievance,
        'maintenance_work': maintenance_work,
    }
    return render(request, 'maintenance/grievance_detail.html', context)

@login_required
@user_passes_test(is_maintenance_staff)
def assign_grievance(request, grievance_id):
    """Assign grievance to maintenance staff"""
    grievance = get_object_or_404(Grievance, grievance_id=grievance_id)
    
    # Only admin can assign grievances
    if request.user.user_type != 'admin':
        messages.error(request, "Only administrators can assign grievances.")
        return redirect('maintenance:grievance_detail', grievance_id=grievance_id)
    
    if request.method == 'POST':
        form = GrievanceAssignForm(request.POST, instance=grievance)
        if form.is_valid():
            grievance = form.save()
            if grievance.assigned_to:
                grievance.status = 'assigned'
                grievance.save()
                messages.success(request, f"Grievance assigned to {grievance.assigned_to.get_full_name() or grievance.assigned_to.username}")
            return redirect('maintenance:grievance_detail', grievance_id=grievance_id)
    else:
        form = GrievanceAssignForm(instance=grievance)
    
    context = {
        'form': form,
        'grievance': grievance,
    }
    return render(request, 'maintenance/assign_grievance.html', context)

@login_required
@user_passes_test(is_maintenance_staff)
def create_maintenance_work(request, grievance_id):
    """Create maintenance work for a grievance"""
    grievance = get_object_or_404(Grievance, grievance_id=grievance_id)
    
    # Check if maintenance work already exists
    if hasattr(grievance, 'maintenance_work'):
        messages.info(request, "Maintenance work already exists for this grievance.")
        return redirect('maintenance:edit_maintenance_work', work_id=grievance.maintenance_work.work_id)
    
    # Check permissions
    if request.user.user_type == 'maintenance' and grievance.assigned_to != request.user:
        messages.error(request, "You can only create work for grievances assigned to you.")
        return redirect('maintenance:grievance_list')
    
    if request.method == 'POST':
        form = MaintenanceWorkForm(request.POST, request.FILES)
        if form.is_valid():
            maintenance_work = form.save(commit=False)
            maintenance_work.grievance = grievance
            maintenance_work.created_by = request.user
            maintenance_work.save()
            
            # Update grievance status
            if maintenance_work.work_status == 'in_progress':
                grievance.status = 'in_progress'
                grievance.save()
            
            messages.success(request, "Maintenance work created successfully!")
            return redirect('maintenance:maintenance_work_detail', work_id=maintenance_work.work_id)
    else:
        form = MaintenanceWorkForm()
    
    context = {
        'form': form,
        'grievance': grievance,
    }
    return render(request, 'maintenance/create_work.html', context)

@login_required
@user_passes_test(is_maintenance_staff)
def edit_maintenance_work(request, work_id):
    """Edit existing maintenance work"""
    maintenance_work = get_object_or_404(MaintenanceWork, work_id=work_id)
    
    # Check permissions
    if request.user.user_type == 'maintenance' and maintenance_work.grievance.assigned_to != request.user:
        messages.error(request, "You can only edit work assigned to you.")
        return redirect('maintenance:grievance_list')
    
    if request.method == 'POST':
        form = MaintenanceWorkForm(request.POST, request.FILES, instance=maintenance_work)
        if form.is_valid():
            form.save()
            messages.success(request, "Maintenance work updated successfully!")
            return redirect('maintenance:maintenance_work_detail', work_id=work_id)
    else:
        form = MaintenanceWorkForm(instance=maintenance_work)
    
    context = {
        'form': form,
        'maintenance_work': maintenance_work,
        'grievance': maintenance_work.grievance,
    }
    return render(request, 'maintenance/edit_work.html', context)

@login_required
@user_passes_test(is_maintenance_staff)
def maintenance_work_detail(request, work_id):
    """View maintenance work details"""
    maintenance_work = get_object_or_404(MaintenanceWork, work_id=work_id)
    
    # Check permissions
    if request.user.user_type == 'maintenance' and maintenance_work.grievance.assigned_to != request.user:
        messages.error(request, "You don't have permission to view this work.")
        return redirect('maintenance:grievance_list')
    
    context = {
        'maintenance_work': maintenance_work,
        'grievance': maintenance_work.grievance,
    }
    return render(request, 'maintenance/work_detail.html', context)

@login_required
@user_passes_test(is_maintenance_staff)
def my_work(request):
    """Show work assigned to current maintenance staff"""
    if request.user.user_type != 'maintenance':
        messages.error(request, "This page is only for maintenance staff.")
        return redirect('maintenance:dashboard')
    
    grievances = Grievance.objects.filter(
        assigned_to=request.user,
        status__in=['assigned', 'in_progress']
    )
    
    context = {
        'grievances': grievances,
    }
    return render(request, 'maintenance/my_work.html', context)

@login_required
@user_passes_test(is_maintenance_staff)
def update_work_status(request, work_id):
    """AJAX endpoint to update work status"""
    if request.method == 'POST':
        maintenance_work = get_object_or_404(MaintenanceWork, work_id=work_id)
        
        # Check permissions
        if request.user.user_type == 'maintenance' and maintenance_work.grievance.assigned_to != request.user:
            return JsonResponse({'success': False, 'error': 'Permission denied'})
        
        new_status = request.POST.get('status')
        if new_status in [choice[0] for choice in MaintenanceWork.WORK_STATUS_CHOICES]:
            maintenance_work.work_status = new_status
            
            if new_status == 'completed':
                maintenance_work.completion_time = timezone.now()
            elif new_status == 'in_progress' and not maintenance_work.start_time:
                maintenance_work.start_time = timezone.now()
            
            maintenance_work.save()
            
            return JsonResponse({
                'success': True,
                'status': maintenance_work.get_work_status_display(),
                'grievance_status': maintenance_work.grievance.get_status_display()
            })
        else:
            return JsonResponse({'success': False, 'error': 'Invalid status'})
    
    return JsonResponse({'success': False, 'error': 'Method not allowed'})