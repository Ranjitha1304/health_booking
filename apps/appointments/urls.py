from django.urls import path
from . import views

urlpatterns = [
    path('book/', views.book_appointment, name='book_appointment'),
    path('list/', views.appointment_list, name='appointment_list'),
    path('update-status/<int:appointment_id>/', views.update_appointment_status, name='update_appointment_status'),
    path('manage-unavailability/', views.manage_unavailability, name='manage_unavailability'),
    path('delete-unavailability/<int:unavailability_id>/', views.delete_unavailability, name='delete_unavailability'),
    path('get-doctors/', views.get_doctors_by_specialization, name='get_doctors_by_specialization'),
    path('get-unavailable-dates/<int:doctor_id>/', views.get_doctor_unavailable_dates, name='get_doctor_unavailable_dates'),
    


]