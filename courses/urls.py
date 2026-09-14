from django.urls import path
from . import views

urlpatterns = [
    # Public
    path('<slug:slug>/', views.course_detail, name='course_detail'),

    # Admin
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/course/create/', views.course_create, name='course_create'),
    path('admin/course/<int:course_id>/edit/', views.course_edit, name='course_edit'),
    path('admin/course/<int:course_id>/delete/', views.course_delete, name='course_delete'),
    path('admin/course/<int:course_id>/students/', views.admin_course_students, name='admin_course_students'),
    path('admin/course/<int:course_id>/lectures/', views.lecture_create, name='lecture_create'),
    path('admin/lecture/<int:lecture_id>/delete/', views.lecture_delete, name='lecture_delete'),

    # Student
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('learn/<slug:slug>/', views.my_learning, name='watch_course'),

    # Payments (Razorpay, UPI-only checkout, fully automatic)
    path('pay/<int:course_id>/', views.initiate_payment, name='initiate_payment'),
    path('pay/verify/<int:payment_id>/', views.verify_payment, name='verify_payment'),
    path('pay/cancelled/<int:payment_id>/', views.payment_cancelled, name='payment_cancelled'),
    path('payment/success/<int:payment_id>/', views.payment_success, name='payment_success'),
    path('payments/history/', views.payment_history, name='payment_history'),
]
