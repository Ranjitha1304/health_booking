from django.db import models

class Profile(models.Model):
    USER_TYPES = (
        ('patient', 'Patient'),
        ('doctor', 'Doctor'),
    )
    
    SPECIALIZATION_CHOICES = (
        ('cardiologist', 'Cardiologist'),
        ('pediatrician', 'Pediatrician'),
        ('general', 'General Physician'),
        ('orthopedic', 'Orthopedic'),
        ('neurologist', 'Neurologist'),
        ('dermatologist', 'Dermatologist'),
        ('psychiatrist', 'Psychiatrist'),
        ('dentist', 'Dentist'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE)
    user_type = models.CharField(max_length=10, choices=USER_TYPES)
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    
    # Doctor-specific fields
    specialization = models.CharField(max_length=50, choices=SPECIALIZATION_CHOICES, blank=True, null=True)
    license_number = models.CharField(max_length=100, blank=True, null=True)
    experience = models.IntegerField(blank=True, null=True, help_text="Years of experience")
    hospital_name = models.CharField(max_length=200, blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    
    bio = models.TextField(blank=True)
    
    class Meta:
        app_label = 'users'
    
    def __str__(self):
        return f"{self.user.username} - {self.user_type} - {self.status}"
    
    def is_approved_doctor(self):
        return self.user_type == 'doctor' and self.status == 'approved'