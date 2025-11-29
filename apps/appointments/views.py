from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from .models import Appointment, DoctorUnavailability
from .forms import AppointmentForm, DoctorUnavailabilityForm
from apps.users.models import Profile

@login_required
def book_appointment(request):
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.patient = request.user
            appointment.status = 'pending'  # New appointments need confirmation
            appointment.save()
            messages.success(request, 'Appointment booked successfully! Waiting for doctor confirmation.')
            return redirect('appointment_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AppointmentForm()
    
    # Get all specializations that have approved doctors
    specializations_with_doctors = Profile.objects.filter(
        user_type='doctor', 
        status='approved'
    ).values_list('specialization', flat=True).distinct()
    
    # Create choices for specializations that actually have doctors
    available_specializations = []
    for spec_code, spec_name in Profile.SPECIALIZATION_CHOICES:
        if spec_code in specializations_with_doctors:
            available_specializations.append((spec_code, spec_name))
    
    # If no specializations available, show message
    if not available_specializations:
        messages.info(request, 'No doctors are currently available. Please check back later.')
    
    return render(request, 'appointments/book.html', {
        'form': form,
        'available_specializations': available_specializations,
    })

@login_required
def appointment_list(request):
    profile = Profile.objects.get(user=request.user)
    
    if profile.user_type == 'patient':
        appointments = Appointment.objects.filter(patient=request.user)
    else:
        appointments = Appointment.objects.filter(doctor=request.user)
    
    return render(request, 'appointments/list.html', {
        'appointments': appointments,
        'user_type': profile.user_type
    })

@login_required
def update_appointment_status(request, appointment_id):
    """Update appointment status (confirm, cancel, complete)"""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    profile = Profile.objects.get(user=request.user)
    
    # Check permissions
    if profile.user_type == 'patient' and appointment.patient != request.user:
        messages.error(request, 'You can only update your own appointments.')
        return redirect('appointment_list')
    
    if profile.user_type == 'doctor' and appointment.doctor != request.user:
        messages.error(request, 'You can only update appointments assigned to you.')
        return redirect('appointment_list')
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        
        if new_status in dict(Appointment.STATUS_CHOICES):
            old_status = appointment.status
            appointment.status = new_status
            appointment.save()
            
            status_display = dict(Appointment.STATUS_CHOICES)[new_status]
            messages.success(request, f'Appointment status updated to {status_display}.')
        else:
            messages.error(request, 'Invalid status.')
    
    return redirect('appointment_list')

@login_required
def manage_unavailability(request):
    """Doctors can manage their unavailable dates"""
    profile = Profile.objects.get(user=request.user)
    
    if profile.user_type != 'doctor':
        messages.error(request, 'Only doctors can manage availability.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = DoctorUnavailabilityForm(request.POST)
        if form.is_valid():
            unavailability = form.save(commit=False)
            unavailability.doctor = request.user
            
            # Check if date is already marked as unavailable
            if DoctorUnavailability.objects.filter(
                doctor=request.user, 
                unavailable_date=unavailability.unavailable_date
            ).exists():
                messages.error(request, 'This date is already marked as unavailable.')
            else:
                unavailability.save()
                messages.success(request, f'Marked {unavailability.unavailable_date} as unavailable.')
                return redirect('manage_unavailability')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = DoctorUnavailabilityForm()
    
    # Get existing unavailability entries
    unavailability_list = DoctorUnavailability.objects.filter(doctor=request.user).order_by('-unavailable_date')
    
    return render(request, 'appointments/manage_unavailability.html', {
        'form': form,
        'unavailability_list': unavailability_list,
    })

@login_required
def delete_unavailability(request, unavailability_id):
    """Remove an unavailability entry"""
    unavailability = get_object_or_404(DoctorUnavailability, id=unavailability_id)
    
    if unavailability.doctor != request.user:
        messages.error(request, 'You can only delete your own unavailability entries.')
        return redirect('manage_unavailability')
    
    if request.method == 'POST':
        date_str = unavailability.unavailable_date.strftime('%Y-%m-%d')
        unavailability.delete()
        messages.success(request, f'Removed unavailability for {date_str}.')
    
    return redirect('manage_unavailability')

@login_required
def get_doctors_by_specialization(request):
    """AJAX view to get doctors by specialization"""
    specialization = request.GET.get('specialization')
    
    if specialization:
        doctors = User.objects.filter(
            profile__user_type='doctor',
            profile__status='approved',
            profile__specialization=specialization
        ).select_related('profile')
        
        doctors_data = []
        for doctor in doctors:
            doctors_data.append({
                'id': doctor.id,
                'name': f"Dr. {doctor.get_full_name()}",
                'specialization': doctor.profile.get_specialization_display(),
                'hospital': doctor.profile.hospital_name,
                'experience': f"{doctor.profile.experience} years experience"
            })
        
        return JsonResponse({'doctors': doctors_data})
    
    return JsonResponse({'doctors': []})

@login_required
def get_doctor_unavailable_dates(request, doctor_id):
    """AJAX view to get doctor's unavailable dates"""
    try:
        doctor = User.objects.get(id=doctor_id, profile__user_type='doctor')
        unavailable_dates = DoctorUnavailability.objects.filter(
            doctor=doctor
        ).values_list('unavailable_date', flat=True)
        
        # Convert dates to string format for JavaScript
        unavailable_dates_list = [date.strftime('%Y-%m-%d') for date in unavailable_dates]
        
        return JsonResponse({'unavailable_dates': unavailable_dates_list})
    except User.DoesNotExist:
        return JsonResponse({'unavailable_dates': []})