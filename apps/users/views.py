from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import authenticate, login
from .forms import CustomUserCreationForm, CustomAuthenticationForm  # Import custom form
from .models import Profile

# Add the home view function
def home(request):
    return render(request, 'home.html')

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()  # Get the user object
            
            # Check if user is doctor or patient
            if user.profile.user_type == 'doctor':
                messages.success(request, 'Registration successful! Your account is pending admin approval. Please wait for approval.')
            else:
                messages.success(request, 'Registration successful! Please login.')
            
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

def custom_login(request):
    if request.method == 'POST':
        # Use CustomAuthenticationForm with request.POST data
        form = CustomAuthenticationForm(request, data=request.POST)
        
        if form.is_valid():
            # Authentication successful
            user = form.get_user()
            
            # Check if user is a doctor pending approval
            if hasattr(user, 'profile') and user.profile.user_type == 'doctor' and user.profile.status == 'pending':
                # Add error to form instead of using messages
                form.add_error(None, 'Your account is pending admin approval. Please wait for approval.')
                return render(request, 'registration/login.html', {'form': form})
            
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name}!')
            return redirect('dashboard')
        # If form is invalid, it will show appropriate error
    else:
        # GET request - create empty form
        form = CustomAuthenticationForm()
    
    return render(request, 'registration/login.html', {'form': form})

@login_required
def dashboard(request):
    try:
        profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        # Create a profile if it doesn't exist
        profile = Profile.objects.create(
            user=request.user,
            user_type='patient',  # Default to patient
            status='approved'
        )
        messages.info(request, 'Your profile has been created automatically.')
    
    if profile.user_type == 'patient':
        # Patient dashboard context
        from apps.appointments.models import Appointment
        from apps.reports.models import MedicalReport
        
        appointments = Appointment.objects.filter(patient=request.user)
        reports = MedicalReport.objects.filter(patient=request.user)
        
        context = {
            'appointments': appointments,
            'reports': reports,
        }
    else:
        # Doctor dashboard context
        from apps.appointments.models import Appointment
        from apps.reports.models import MedicalReport
        
        appointments = Appointment.objects.filter(doctor=request.user)
        shared_reports = MedicalReport.objects.filter(shared_with=request.user)
        context = {
            'appointments': appointments,
            'shared_reports': shared_reports,
        }
    
    context['profile'] = profile
    return render(request, 'dashboard.html', context)


from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User

@staff_member_required
def admin_dashboard(request):
    """Custom admin dashboard"""
    # Get statistics
    total_users = User.objects.count()
    total_patients = Profile.objects.filter(user_type='patient').count()
    total_doctors = Profile.objects.filter(user_type='doctor').count()
    pending_doctors = Profile.objects.filter(user_type='doctor', status='pending').count()
    approved_doctors = Profile.objects.filter(user_type='doctor', status='approved').count()
    
    # Get recent pending doctors
    pending_doctor_list = Profile.objects.filter(user_type='doctor', status='pending').select_related('user')
    
    # Get recent users
    recent_users = User.objects.order_by('-date_joined')[:10]
    
    context = {
        'total_users': total_users,
        'total_patients': total_patients,
        'total_doctors': total_doctors,
        'pending_doctors': pending_doctors,
        'approved_doctors': approved_doctors,
        'pending_doctor_list': pending_doctor_list,
        'recent_users': recent_users,
    }
    return render(request, 'admin/dashboard.html', context)

@staff_member_required
def admin_doctor_approvals(request):
    """Manage doctor approvals"""
    pending_doctors = Profile.objects.filter(user_type='doctor', status='pending').select_related('user')
    approved_doctors = Profile.objects.filter(user_type='doctor', status='approved').select_related('user')
    rejected_doctors = Profile.objects.filter(user_type='doctor', status='rejected').select_related('user')
    
    if request.method == 'POST':
        doctor_id = request.POST.get('doctor_id')
        action = request.POST.get('action')
        
        try:
            profile = Profile.objects.get(id=doctor_id)
            if action == 'approve':
                profile.status = 'approved'
                profile.save()
                messages.success(request, f'Doctor {profile.user.get_full_name()} has been approved!')
            elif action == 'reject':
                profile.status = 'rejected'
                profile.save()
                messages.warning(request, f'Doctor {profile.user.get_full_name()} has been rejected.')
        except Profile.DoesNotExist:
            messages.error(request, 'Doctor not found.')
        
        return redirect('admin_doctor_approvals')
    
    context = {
        'pending_doctors': pending_doctors,
        'approved_doctors': approved_doctors,
        'rejected_doctors': rejected_doctors,
    }
    return render(request, 'admin/doctor_approvals.html', context)

@staff_member_required
def admin_user_management(request):
    """Manage all users"""
    users = User.objects.all().select_related('profile').order_by('-date_joined')
    
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        action = request.POST.get('action')
        
        try:
            user = User.objects.get(id=user_id)
            if action == 'deactivate':
                user.is_active = False
                user.save()
                messages.warning(request, f'User {user.username} has been deactivated.')
            elif action == 'activate':
                user.is_active = True
                user.save()
                messages.success(request, f'User {user.username} has been activated.')
            elif action == 'delete':
                user.delete()
                messages.error(request, f'User {user.username} has been deleted.')
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
        
        return redirect('admin_user_management')
    
    context = {
        'users': users,
    }
    return render(request, 'admin/user_management.html', context)

@staff_member_required
def admin_appointments(request):
    """View all appointments"""
    from apps.appointments.models import Appointment
    appointments = Appointment.objects.all().select_related('patient', 'doctor').order_by('-appointment_date')
    
    context = {
        'appointments': appointments,
    }
    return render(request, 'admin/appointments.html', context)

@staff_member_required
def admin_reports(request):
    """View all medical reports"""
    from apps.reports.models import MedicalReport
    reports = MedicalReport.objects.all().select_related('patient', 'shared_with').order_by('-uploaded_at')
    
    context = {
        'reports': reports,
    }
    return render(request, 'admin/reports.html', context)