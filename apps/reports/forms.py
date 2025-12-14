from django import forms
from django.contrib.auth.models import User
from .models import MedicalReport, DoctorResponse
from apps.users.models import Profile
import os

class MedicalReportForm(forms.ModelForm):
    category = forms.ChoiceField(
        choices=(
            ('', 'Select a category...'),
            ('cardiologist', 'Cardiology'),
            ('pediatrician', 'Pediatrics'),
            ('general', 'General Medicine'),
            ('orthopedic', 'Orthopedics'),
            ('neurologist', 'Neurology'),
            ('dermatologist', 'Dermatology'),
            ('psychiatrist', 'Psychiatry'),
            ('dentist', 'Dentistry'),
        ),
        required=True,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'category-select'})
    )
    
    shared_with = forms.ModelChoiceField(
        queryset=User.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'doctor-select'})
    )
    
    report_file = forms.FileField(
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        label='Report File *'
    )
    
    class Meta:
        model = MedicalReport
        fields = ['title', 'description', 'category', 'shared_with', 'report_file']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initially set empty doctor queryset
        self.fields['shared_with'].queryset = User.objects.none()
        
        # If form is bound with data, filter doctors based on category
        if 'category' in self.data:
            try:
                category = self.data.get('category')
                if category:
                    approved_doctors = User.objects.filter(
                        profile__user_type='doctor', 
                        profile__status='approved',
                        profile__specialization=category
                    )
                    self.fields['shared_with'].queryset = approved_doctors
            except (ValueError, TypeError):
                pass
    
    def clean_report_file(self):
        report_file = self.cleaned_data.get('report_file')
        
        if not report_file:
            raise forms.ValidationError("Report file is required.")
        
        # File size validation (10MB = 10 * 1024 * 1024 bytes)
        max_size = 10 * 1024 * 1024  # 10MB
        if report_file.size > max_size:
            raise forms.ValidationError(f"File size exceeds 10MB limit. Your file is {report_file.size / (1024*1024):.1f}MB.")
        
        # File format validation
        allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
        file_name = report_file.name
        file_extension = os.path.splitext(file_name)[1].lower()
        
        if file_extension not in allowed_extensions:
            raise forms.ValidationError(
                f"Unsupported file format. Allowed formats: {', '.join(allowed_extensions)}. "
                f"Your file: {file_extension}"
            )
        
        # Additional validation for specific file types
        if file_extension == '.pdf':
            # Check if it's actually a PDF (basic check)
            if not file_name.lower().endswith('.pdf'):
                raise forms.ValidationError("Invalid PDF file.")
        elif file_extension in ['.jpg', '.jpeg', '.png']:
            # Check if it's an image (basic check by extension)
            if not (file_name.lower().endswith(('.jpg', '.jpeg', '.png'))):
                raise forms.ValidationError("Invalid image file.")
        
        return report_file

class DoctorResponseForm(forms.ModelForm):
    prescription = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 6, 
            'class': 'form-control prescription-input',
            'placeholder': '''Enter prescription details. For better PDF formatting:
- One medication per line
- Use format: Medication Name | Dosage | Frequency | Duration
Example:
Paracetamol | 500mg | Once daily after meals | 5 days
Amoxicillin | 250mg | Every 8 hours | 7 days
OR
Simply list medications with details in paragraphs'''
        }),
        label='Prescription & Medications'
    )
    
    class Meta:
        model = DoctorResponse
        fields = ['diagnosis', 'prescription', 'recommendations', 'advice']
        widgets = {
            'diagnosis': forms.Textarea(attrs={
                'rows': 5, 
                'class': 'form-control', 
                'placeholder': 'Enter detailed diagnosis and medical findings...'
            }),
            'recommendations': forms.Textarea(attrs={
                'rows': 4, 
                'class': 'form-control', 
                'placeholder': 'Enter recommendations for tests, follow-ups, or lifestyle changes...'
            }),
            'advice': forms.Textarea(attrs={
                'rows': 3, 
                'class': 'form-control', 
                'placeholder': 'Enter general medical advice and precautions...'
            }),
        }
        labels = {
            'diagnosis': 'Diagnosis & Findings',
            'recommendations': 'Recommendations & Follow-up',
            'advice': 'Medical Advice & Precautions',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add help text
        # self.fields['prescription'].help_text = 'Tip: Use pipe-separated format (|) for better PDF table formatting'