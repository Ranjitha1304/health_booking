from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_report, name='upload_report'),
    path('list/', views.report_list, name='report_list'),
    path('detail/<int:report_id>/', views.report_detail, name='report_detail'),
    path('response/<int:report_id>/', views.add_doctor_response, name='add_doctor_response'),
    path('get-doctors/', views.get_doctors_by_category, name='get_doctors_by_category'),
    path('edit-response/<int:report_id>/', views.edit_doctor_response, name='edit_doctor_response'),
    

]