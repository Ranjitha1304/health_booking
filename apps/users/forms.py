from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    user_type = forms.ChoiceField(choices=Profile.USER_TYPES, widget=forms.RadioSelect)
    phone = forms.CharField(max_length=15, required=False)
    
    # Doctor-specific fields
    specialization = forms.ChoiceField(choices=Profile.SPECIALIZATION_CHOICES, required=False)
    license_number = forms.CharField(max_length=100, required=False)
    experience = forms.IntegerField(required=False, min_value=0)
    hospital_name = forms.CharField(max_length=200, required=False)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'first_name', 'last_name')
    
    def clean(self):
        cleaned_data = super().clean()
        user_type = cleaned_data.get('user_type')
        
        if user_type == 'doctor':
            specialization = cleaned_data.get('specialization')
            license_number = cleaned_data.get('license_number')
            experience = cleaned_data.get('experience')
            hospital_name = cleaned_data.get('hospital_name')
            
            if not specialization:
                self.add_error('specialization', 'Specialization is required for doctors')
            if not license_number:
                self.add_error('license_number', 'License number is required for doctors')
            if not experience:
                self.add_error('experience', 'Experience is required for doctors')
            if not hospital_name:
                self.add_error('hospital_name', 'Hospital name is required for doctors')
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            
            # Update the existing profile (created by signals) instead of creating a new one
            profile = user.profile
            profile.user_type = self.cleaned_data['user_type']
            profile.phone = self.cleaned_data['phone']
            
            if self.cleaned_data['user_type'] == 'doctor':
                profile.specialization = self.cleaned_data['specialization']
                profile.license_number = self.cleaned_data['license_number']
                profile.experience = self.cleaned_data['experience']
                profile.hospital_name = self.cleaned_data['hospital_name']
                profile.status = 'pending'  # Doctors need approval
            else:
                profile.status = 'approved'  # Patients are auto-approved
            
            profile.save()
            
        return user