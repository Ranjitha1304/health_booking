from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

from apps.users import views as user_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', user_views.home, name='home'),
    # Use custom login from users app
    path('accounts/login/', user_views.custom_login, name='login'),  # Custom login
    path('accounts/', include('django.contrib.auth.urls')),  # Keep other auth URLs
    path('users/', include('apps.users.urls')),
    path('appointments/', include('apps.appointments.urls')),
    path('reports/', include('apps.reports.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)