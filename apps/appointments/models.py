from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta

class DoctorUnavailability(models.Model):
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'profile__user_type': 'doctor'})
    unavailable_date = models.DateField()
    reason = models.CharField(max_length=200, blank=True, help_text="Reason for unavailability (e.g., Vacation, Leave)")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        app_label = 'appointments'
        unique_together = ['doctor', 'unavailable_date']
        verbose_name_plural = 'Doctor Unavailabilities'
    
    def __str__(self):
        return f"Dr. {self.doctor.last_name} - {self.unavailable_date} - {self.reason}"

class Appointment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending Confirmation'),
        ('confirmed', 'Confirmed'),
        ('scheduled', 'Scheduled'),  # For backward compatibility
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='patient_appointments')
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='doctor_appointments')
    appointment_date = models.DateTimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'appointments'
        ordering = ['-appointment_date']
    
    def __str__(self):
        return f"{self.patient.username} with Dr. {self.doctor.last_name} on {self.appointment_date}"
    
    def clean(self):
        # Validate appointment date is not in the past
        if self.appointment_date and self.appointment_date < timezone.now():
            raise ValidationError('Cannot book appointments in the past.')
        
        # Validate appointment date is within 30 days
        max_booking_date = timezone.now() + timedelta(days=30)
        if self.appointment_date and self.appointment_date > max_booking_date:
            raise ValidationError('Appointments can only be booked up to 30 days in advance.')
        
        # Check if doctor is unavailable on this date
        if self.doctor and self.appointment_date:
            unavailable_dates = DoctorUnavailability.objects.filter(
                doctor=self.doctor,
                unavailable_date=self.appointment_date.date()
            )
            if unavailable_dates.exists():
                raise ValidationError('Doctor is not available on the selected date.')
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)