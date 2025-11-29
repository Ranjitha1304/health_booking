from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Profile

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'

class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_user_type', 'get_status', 'is_staff')
    list_select_related = ('profile',)
    
    def get_user_type(self, instance):
        return instance.profile.user_type
    get_user_type.short_description = 'User Type'
    
    def get_status(self, instance):
        return instance.profile.status
    get_status.short_description = 'Status'
    
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super().get_inline_instances(request, obj)

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'user_type', 'specialization', 'status', 'hospital_name']
    list_filter = ['user_type', 'status', 'specialization']
    list_editable = ['status']
    actions = ['approve_doctors', 'reject_doctors']
    
    def approve_doctors(self, request, queryset):
        queryset.filter(user_type='doctor').update(status='approved')
        self.message_user(request, "Selected doctors have been approved.")
    approve_doctors.short_description = "Approve selected doctors"
    
    def reject_doctors(self, request, queryset):
        queryset.filter(user_type='doctor').update(status='rejected')
        self.message_user(request, "Selected doctors have been rejected.")
    reject_doctors.short_description = "Reject selected doctors"