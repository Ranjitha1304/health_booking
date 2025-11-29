from django import forms
from django.contrib.auth.models import User
from .models import MedicalReport, DoctorResponse
from apps.users.models import Profile

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
    
    class Meta:
        model = MedicalReport
        fields = ['title', 'description', 'category', 'shared_with', 'report_file']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'report_file': forms.FileInput(attrs={'class': 'form-control'}),
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

class DoctorResponseForm(forms.ModelForm):
    class Meta:
        model = DoctorResponse
        fields = ['diagnosis', 'prescription', 'recommendations', 'advice']
        widgets = {
            'diagnosis': forms.Textarea(attrs={
                'rows': 4, 
                'class': 'form-control', 
                'placeholder': 'Enter your diagnosis and medical findings...'
            }),
            'prescription': forms.Textarea(attrs={
                'rows': 5, 
                'class': 'form-control', 
                'placeholder': 'Enter prescription details, medications, dosage, and instructions...'
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
            'prescription': 'Prescription & Medications',
            'recommendations': 'Recommendations & Follow-up',
            'advice': 'Medical Advice & Precautions',
        }