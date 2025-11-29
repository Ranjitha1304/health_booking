from apps.users.models import Profile

def admin_context(request):
    if request.user.is_authenticated and request.user.is_staff:
        pending_count = Profile.objects.filter(user_type='doctor', status='pending').count()
        return {'pending_count': pending_count}
    return {}