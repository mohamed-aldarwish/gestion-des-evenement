from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from accounts.views import login_view

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', include('events.urls')),

    path('tickets/', include('tickets.urls')),
    path('events/', include('events.urls')),
    path('accounts/', include('accounts.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('registrations/', include('registrations.urls')),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )