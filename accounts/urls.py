from django.urls import path
from . import views

urlpatterns = [
    path('student/register/', views.student_register, name='student_register'),
    path('student/login/', views.student_login, name='student_login'),
    path('admin/register/', views.admin_register, name='admin_register'),
    path('admin/login/', views.admin_login, name='admin_login'),
    path('logout/', views.user_logout, name='logout'),
    path('delete-account/', views.delete_account, name='delete_account'),
]
