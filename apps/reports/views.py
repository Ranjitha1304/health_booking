from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponse
from .models import MedicalReport, DoctorResponse
from .forms import MedicalReportForm, DoctorResponseForm
from .pdf_utils import create_medical_response_pdf, generate_pdf_filename
from apps.users.models import Profile


@login_required
def upload_report(request):
    if request.method == 'POST':
        form = MedicalReportForm(request.POST, request.FILES)
        if form.is_valid():
            report = form.save(commit=False)
            report.patient = request.user
            report.analysis_results = "Report uploaded successfully. Basic analysis feature available for text-based reports."
            report.save()
            
            if report.shared_with:
                messages.success(request, f'Report uploaded and shared with Dr. {report.shared_with.last_name}!')
            else:
                messages.success(request, 'Report uploaded successfully!')
                
            return redirect('report_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = MedicalReportForm()
    
    # Get all categories that have approved doctors
    categories_with_doctors = Profile.objects.filter(
        user_type='doctor', 
        status='approved'
    ).values_list('specialization', flat=True).distinct()
    
    # Create choices for categories that actually have doctors
    available_categories = []
    for spec_code, spec_name in Profile.SPECIALIZATION_CHOICES:
        if spec_code in categories_with_doctors:
            available_categories.append((spec_code, spec_name))
    
    return render(request, 'reports/upload.html', {
        'form': form,
        'available_categories': available_categories,
    })

@login_required
def report_list(request):
    from apps.users.models import Profile
    profile = Profile.objects.get(user=request.user)
    
    if profile.user_type == 'patient':
        reports = MedicalReport.objects.filter(patient=request.user)
        show_upload_button = True  # Patients can upload reports
    else:  # Doctor
        # Show reports shared with this doctor
        reports = MedicalReport.objects.filter(shared_with=request.user)
        show_upload_button = False  # Doctors cannot upload reports
    
    return render(request, 'reports/list.html', {
        'reports': reports,
        'user_type': profile.user_type,
        'show_upload_button': show_upload_button,  # Pass this to template
    })

@login_required
def report_detail(request, report_id):
    from apps.users.models import Profile
    
    # Allow admin/staff to view any report
    if request.user.is_staff:
        report = get_object_or_404(MedicalReport, id=report_id)
        user_type = 'admin'
        can_respond = False
    else:
        profile = Profile.objects.get(user=request.user)
        
        if profile.user_type == 'patient':
            report = get_object_or_404(MedicalReport, id=report_id, patient=request.user)
            can_respond = False
        else:
            report = get_object_or_404(MedicalReport, id=report_id, shared_with=request.user)
            can_respond = not hasattr(report, 'doctor_response')
        
        user_type = profile.user_type
    
    # Check if there's already a response
    response = getattr(report, 'doctor_response', None)
    
    # Only create response_form if doctor can respond AND user is a doctor
    if can_respond and user_type == 'doctor':
        response_form = DoctorResponseForm()
    else:
        response_form = None
    
    return render(request, 'reports/detail.html', {
        'report': report,
        'user_type': user_type,
        'response_form': response_form,
        'existing_response': response,
        'can_respond': can_respond,
    })

@login_required
def add_doctor_response(request, report_id):
    if request.method == 'POST':
        from apps.users.models import Profile
        profile = Profile.objects.get(user=request.user)
        
        if profile.user_type != 'doctor':
            messages.error(request, 'Only doctors can add responses.')
            return redirect('dashboard')
        
        report = get_object_or_404(MedicalReport, id=report_id, shared_with=request.user)
        
        if hasattr(report, 'doctor_response'):
            messages.error(request, 'Response already exists for this report.')
            return redirect('report_detail', report_id=report_id)
        
        form = DoctorResponseForm(request.POST)
        if form.is_valid():
            response = form.save(commit=False)
            response.report = report
            response.doctor = request.user
            response.save()
            messages.success(request, 'Your response has been sent to the patient successfully!')
            return redirect('report_detail', report_id=report_id)
        else:
            messages.error(request, 'Please correct the errors in the form.')
            return render(request, 'reports/detail.html', {
                'report': report,
                'user_type': profile.user_type,
                'response_form': form,
                'can_respond': True,
            })
    
    return redirect('report_detail', report_id=report_id)

@login_required
def edit_doctor_response(request, report_id):
    """Allow doctors to edit their existing responses"""
    if request.method == 'POST':
        from apps.users.models import Profile
        profile = Profile.objects.get(user=request.user)
        
        if profile.user_type != 'doctor':
            messages.error(request, 'Only doctors can edit responses.')
            return redirect('dashboard')
        
        report = get_object_or_404(MedicalReport, id=report_id, shared_with=request.user)
        
        if not hasattr(report, 'doctor_response'):
            messages.error(request, 'No response found to edit.')
            return redirect('report_detail', report_id=report_id)
        
        if report.doctor_response.doctor != request.user:
            messages.error(request, 'You can only edit your own responses.')
            return redirect('report_detail', report_id=report_id)
        
        form = DoctorResponseForm(request.POST, instance=report.doctor_response)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your response has been updated successfully!')
            return redirect('report_detail', report_id=report_id)
        else:
            messages.error(request, 'Please correct the errors in the form.')
    
    return redirect('report_detail', report_id=report_id)

@login_required
def get_doctors_by_category(request):
    """AJAX view to get doctors by category"""
    category = request.GET.get('category')
    
    if category:
        doctors = User.objects.filter(
            profile__user_type='doctor',
            profile__status='approved',
            profile__specialization=category
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
def download_response_pdf(request, report_id):
    """Download doctor's response as a professional PDF"""
    # Get the report
    if request.user.is_staff:
        report = get_object_or_404(MedicalReport, id=report_id)
    else:
        # For patients, they can only download their own reports
        report = get_object_or_404(MedicalReport, id=report_id, patient=request.user)
    
    # Check if there's a response
    if not hasattr(report, 'doctor_response'):
        messages.error(request, 'No doctor response available for this report.')
        return redirect('report_detail', report_id=report_id)
    
    response = report.doctor_response
    
    # Get additional information for the PDF - handle missing Profile gracefully
    try:
        patient_profile = Profile.objects.get(user=report.patient)
        patient_info = {
            'full_name': report.patient.get_full_name() or report.patient.username,
            'contact': patient_profile.phone if patient_profile.phone else 'Not specified',
            'address': patient_profile.address if patient_profile.address else 'Not specified',
        }
    except Profile.DoesNotExist:
        patient_info = {
            'full_name': report.patient.get_full_name() or report.patient.username,
            'contact': 'Not specified',
            'address': 'Not specified',
        }
    
    try:
        doctor_profile = Profile.objects.get(user=response.doctor)
        doctor_info = {
            'full_name': response.doctor.get_full_name() or response.doctor.username,
            'specialization': doctor_profile.get_specialization_display() if doctor_profile.specialization else 'Consultant',
            'license': doctor_profile.license_number if doctor_profile.license_number else f'MED-{response.doctor.id:05d}',
            'hospital': doctor_profile.hospital_name if doctor_profile.hospital_name else 'Not specified',
            'experience': f"{doctor_profile.experience} years" if doctor_profile.experience else 'Not specified',
        }
    except Profile.DoesNotExist:
        doctor_info = {
            'full_name': response.doctor.get_full_name() or response.doctor.username,
            'specialization': 'Consultant',
            'license': f'MED-{response.doctor.id:05d}',
            'hospital': 'Not specified',
            'experience': 'Not specified',
        }
    
    # Generate PDF
    pdf_content = create_medical_response_pdf(report, response, patient_info, doctor_info)
    
    # Create response
    response_pdf = HttpResponse(pdf_content, content_type='application/pdf')
    filename = generate_pdf_filename(report, response)
    response_pdf['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response_pdf