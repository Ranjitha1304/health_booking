from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('login/', views.custom_login, name='login'),
    # Admin URLs
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/doctor-approvals/', views.admin_doctor_approvals, name='admin_doctor_approvals'),
    path('admin/user-management/', views.admin_user_management, name='admin_user_management'),
    path('admin/appointments/', views.admin_appointments, name='admin_appointments'),
    path('admin/reports/', views.admin_reports, name='admin_reports'),
]