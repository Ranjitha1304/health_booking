from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile
import re
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext_lazy as _

class CustomAuthenticationForm(AuthenticationForm):
    error_messages = {
        'invalid_login': _(
            "Invalid username or password. Please try again."
        ),
        'inactive': _("This account is inactive."),
    }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to form fields
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your username'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control', 
            'placeholder': 'Enter your password'
        })

# Custom validator for phone number
def validate_phone_number(value):
    value = value.strip()
    if not value:
        return  # Allow empty phone numbers as they are not required
    
    # Check if it contains exactly 10 digits
    if not value.isdigit():
        raise forms.ValidationError("Phone number must contain only digits.")
    
    if len(value) != 10:
        raise forms.ValidationError("Phone number must be exactly 10 digits.")
    
    # Check if it starts with 7, 8, or 9
    if value[0] not in ['7', '8', '9']:
        raise forms.ValidationError("Phone number must start with 7, 8, or 9.")

# Custom validator for license number (for new registrations only)
def validate_license_number_for_new(value):
    """Only validate if value is provided"""
    if not value:
        return  # Allow empty as it will be validated in clean() method
    
    # Check if it contains only digits
    if not value.isdigit():
        raise forms.ValidationError("License number must contain only numbers.")
    
    # Check length
    if len(value) < 4:
        raise forms.ValidationError("License number must be at least 4 digits.")
    
    if len(value) > 12:
        raise forms.ValidationError("License number cannot exceed 12 digits.")

# Custom validator for hospital name
def validate_hospital_name(value):
    if not value:
        return  # Allow empty as it will be validated in clean() method
    
    # Check length
    if len(value) < 3:
        raise forms.ValidationError("Hospital name must be at least 3 characters.")
    
    if len(value) > 100:
        raise forms.ValidationError("Hospital name cannot exceed 100 characters.")
    
    # Check if it's only numbers
    if value.isdigit():
        raise forms.ValidationError("Hospital name cannot be only numbers.")
    
    # Check if it contains only allowed characters
    # Remove allowed special characters and spaces to check what's left
    temp_value = value
    # Remove allowed special characters
    temp_value = re.sub(r'[ .,\-&\'\/]', '', temp_value)
    
    # If after removing allowed characters, it's empty, it means it contains only symbols
    if not temp_value:
        raise forms.ValidationError("Hospital name cannot contain only symbols.")
    
    # Check if what remains contains only letters and numbers
    if not re.match(r'^[A-Za-z0-9]*$', temp_value):
        raise forms.ValidationError("Hospital name contains invalid characters.")
    
    # Check if it's only symbols (no letters or numbers)
    # Remove all non-alphanumeric characters
    alphanumeric_only = re.sub(r'[^A-Za-z0-9]', '', value)
    if not alphanumeric_only:
        raise forms.ValidationError("Hospital name must contain letters or numbers.")

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    user_type = forms.ChoiceField(choices=Profile.USER_TYPES, widget=forms.RadioSelect)
    phone = forms.CharField(max_length=15, required=False, validators=[validate_phone_number])
    
    # Doctor-specific fields
    specialization = forms.ChoiceField(choices=Profile.SPECIALIZATION_CHOICES, required=False)
    license_number = forms.CharField(max_length=100, required=False)
    experience = forms.IntegerField(required=False, min_value=0)
    hospital_name = forms.CharField(max_length=200, required=False, validators=[validate_hospital_name])
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'first_name', 'last_name')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Check if this is an existing user (for edit forms)
        self.is_new_user = self.instance.pk is None
    
    def clean_username(self):
        """Normalize username to lowercase to make it case-insensitive"""
        username = self.cleaned_data.get('username')
        if username:
            username = username.lower()
        return username
    
    def clean_license_number(self):
        """Validate license number only for new doctor registrations"""
        license_number = self.cleaned_data.get('license_number', '').strip()
        user_type = self.data.get('user_type') or self.initial.get('user_type')
        
        # For existing users, don't validate format (backward compatibility)
        if not self.is_new_user:
            return license_number
        
        # For new registrations, only validate if user_type is doctor
        if user_type == 'doctor' and license_number:
            # Check if it contains only digits
            if not license_number.isdigit():
                raise forms.ValidationError("License number must contain only numbers.")
            
            # Check length
            if len(license_number) < 4:
                raise forms.ValidationError("License number must be at least 4 digits.")
            
            if len(license_number) > 12:
                raise forms.ValidationError("License number cannot exceed 12 digits.")
        
        return license_number
    
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
            elif self.is_new_user and license_number:
                # Only validate format for new registrations
                if not license_number.isdigit():
                    self.add_error('license_number', 'License number must contain only numbers.')
                elif len(license_number) < 4 or len(license_number) > 12:
                    self.add_error('license_number', 'License number must be between 4 and 12 digits.')
            
            if not experience:
                self.add_error('experience', 'Experience is required for doctors')
            if not hospital_name:
                self.add_error('hospital_name', 'Hospital name is required for doctors')
            elif hospital_name:
                # Hospital name validation (applies to both new and existing)
                if len(hospital_name) < 3 or len(hospital_name) > 100:
                    self.add_error('hospital_name', 'Hospital name must be between 3 and 100 characters.')
                elif hospital_name.isdigit():
                    self.add_error('hospital_name', 'Hospital name cannot be only numbers.')
                else:
                    # Check for invalid patterns
                    temp_name = hospital_name
                    # Remove allowed special characters
                    temp_name = re.sub(r'[ .,\-&\'\/]', '', temp_name)
                    if not temp_name:
                        self.add_error('hospital_name', 'Hospital name cannot contain only symbols.')
                    elif not re.match(r'^[A-Za-z0-9]*$', temp_name):
                        self.add_error('hospital_name', 'Hospital name contains invalid characters.')
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        # Ensure username is saved in lowercase
        user.username = self.cleaned_data['username'].lower()
        
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