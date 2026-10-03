from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from courses.views import home

urlpatterns = [
    path('django-admin/', admin.site.urls),  # Django's built-in admin (superuser only)
    path('', home, name='home'),
    path('contact/', TemplateView.as_view(template_name='pages/contact.html'), name='contact'),
    path('refund-policy/', TemplateView.as_view(template_name='pages/refund_policy.html'), name='refund_policy'),
    path('privacy-policy/', TemplateView.as_view(template_name='pages/privacy_policy.html'), name='privacy_policy'),
    path('terms-and-conditions/', TemplateView.as_view(template_name='pages/terms.html'), name='terms'),
    path('accounts/', include('accounts.urls')),
    path('courses/', include('courses.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
