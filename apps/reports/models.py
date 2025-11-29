from django.db import models
from django.contrib.auth.models import User

class MedicalReport(models.Model):
    patient = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    report_file = models.FileField(upload_to='medical_reports/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    analysis_results = models.TextField(blank=True)

    # Category/Specialization for the report
    category = models.CharField(
        max_length=50, 
        choices=(
            ('cardiologist', 'Cardiology'),
            ('pediatrician', 'Pediatrics'),
            ('general', 'General Medicine'),
            ('orthopedic', 'Orthopedics'),
            ('neurologist', 'Neurology'),
            ('dermatologist', 'Dermatology'),
            ('psychiatrist', 'Psychiatry'),
            ('dentist', 'Dentistry'),
        ),
        blank=True,
        null=True
    )
    
    # Share with specific doctor
    shared_with = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                  related_name='shared_reports', limit_choices_to={'profile__user_type': 'doctor', 'profile__status': 'approved'})
    
    class Meta:
        app_label = 'reports'
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.title} - {self.patient.username}"

class DoctorResponse(models.Model):
    report = models.OneToOneField(MedicalReport, on_delete=models.CASCADE, related_name='doctor_response')
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'profile__user_type': 'doctor'})
    prescription = models.TextField(help_text="Prescription details and medications")
    diagnosis = models.TextField(help_text="Diagnosis and findings")
    recommendations = models.TextField(help_text="Additional recommendations and follow-up instructions")
    advice = models.TextField(help_text="General medical advice", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'reports'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Response for {self.report.title} by Dr. {self.doctor.last_name}"