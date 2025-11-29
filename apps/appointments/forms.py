from django import forms
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from .models import Appointment, DoctorUnavailability
from apps.users.models import Profile

class AppointmentForm(forms.ModelForm):
    specialization = forms.ChoiceField(
        choices=Profile.SPECIALIZATION_CHOICES, 
        required=True,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'specialization-select'})
    )
    
    doctor = forms.ModelChoiceField(
        queryset=User.objects.none(),
        required=True,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'doctor-select'})
    )
    
    class Meta:
        model = Appointment
        fields = ['specialization', 'doctor', 'appointment_date', 'reason']
        widgets = {
            'appointment_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local', 
                'class': 'form-control',
                'min': '',  # Will be set via JavaScript
                'max': '',  # Will be set via JavaScript
            }),
            'reason': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initially set empty doctor queryset
        self.fields['doctor'].queryset = User.objects.none()
        
        # Set min and max dates for the date picker
        now = timezone.now()
        min_date = now.strftime('%Y-%m-%dT%H:%M')
        max_date = (now + timedelta(days=30)).strftime('%Y-%m-%dT%H:%M')
        
        self.fields['appointment_date'].widget.attrs['min'] = min_date
        self.fields['appointment_date'].widget.attrs['max'] = max_date
        
        # If form is bound with data, filter doctors based on specialization
        if 'specialization' in self.data:
            try:
                specialization = self.data.get('specialization')
                approved_doctors = User.objects.filter(
                    profile__user_type='doctor', 
                    profile__status='approved',
                    profile__specialization=specialization
                )
                self.fields['doctor'].queryset = approved_doctors
            except (ValueError, TypeError):
                pass
    
    def clean_appointment_date(self):
        appointment_date = self.cleaned_data.get('appointment_date')
        
        if appointment_date:
            # Check if date is within allowed range
            now = timezone.now()
            max_booking_date = now + timedelta(days=30)
            
            if appointment_date < now:
                raise forms.ValidationError("Cannot book appointments in the past.")
            
            if appointment_date > max_booking_date:
                raise forms.ValidationError("Appointments can only be booked up to 30 days in advance.")
        
        return appointment_date

    # ADD THIS CLEAN METHOD FOR DOCTOR UNAVAILABILITY VALIDATION
    def clean(self):
        cleaned_data = super().clean()
        doctor = cleaned_data.get('doctor')
        appointment_date = cleaned_data.get('appointment_date')
        
        if doctor and appointment_date:
            # Check if doctor is unavailable on this date
            unavailable_dates = DoctorUnavailability.objects.filter(
                doctor=doctor,
                unavailable_date=appointment_date.date()
            )
            if unavailable_dates.exists():
                reason = unavailable_dates.first().reason
                error_msg = f"Doctor is not available on {appointment_date.date()}"
                if reason:
                    error_msg += f" ({reason})"
                raise forms.ValidationError(error_msg)
        
        return cleaned_data

class DoctorUnavailabilityForm(forms.ModelForm):
    class Meta:
        model = DoctorUnavailability
        fields = ['unavailable_date', 'reason']
        widgets = {
            'unavailable_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'min': '',  # Will be set via JavaScript
            }),
            'reason': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Vacation, Sick Leave, Conference'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set min date to today
        from django.utils import timezone
        min_date = timezone.now().strftime('%Y-%m-%d')
        self.fields['unavailable_date'].widget.attrs['min'] = min_date
    
    def clean_unavailable_date(self):
        unavailable_date = self.cleaned_data.get('unavailable_date')
        
        if unavailable_date:
            from django.utils import timezone
            if unavailable_date < timezone.now().date():
                raise forms.ValidationError("Cannot mark past dates as unavailable.")
        
        return unavailable_date