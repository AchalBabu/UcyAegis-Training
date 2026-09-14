from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from courses.views import home

urlpatterns = [
    path('django-admin/', admin.site.urls),  # Django's built-in admin (superuser only)
    path('', home, name='home'),
    path('accounts/', include('accounts.urls')),
    path('courses/', include('courses.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
