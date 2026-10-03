from django.urls import path
from . import views


urlpatterns = [

    # =====================================================
    # ADMIN
    # =====================================================

    path(
        'admin/dashboard/',
        views.admin_dashboard,
        name='admin_dashboard'
    ),

    path(
        'admin/course/create/',
        views.course_create,
        name='course_create'
    ),

    path(
        'admin/course/<int:course_id>/edit/',
        views.course_edit,
        name='course_edit'
    ),

    path(
        'admin/course/<int:course_id>/delete/',
        views.course_delete,
        name='course_delete'
    ),

    path(
        'admin/course/<int:course_id>/students/',
        views.admin_course_students,
        name='admin_course_students'
    ),

    path(
        'admin/course/<int:course_id>/student/<int:student_id>/progress/',
        views.admin_student_progress,
        name='admin_student_progress'
    ),

    path(
        'admin/course/<int:course_id>/lectures/',
        views.lecture_create,
        name='lecture_create'
    ),

    path(
        'admin/course/<int:course_id>/assignments/',
        views.assignment_manage,
        name='assignment_manage'
    ),

    path(
        'admin/lecture/<int:lecture_id>/delete/',
        views.lecture_delete,
        name='lecture_delete'
    ),

    # =====================================================
    # COURSE RESOURCES
    # =====================================================

    path(
        'admin/course/<int:course_id>/resources/',
        views.course_resources,
        name='course_resources'
    ),

    path(
        'admin/certificate/<int:certificate_id>/delete/',
        views.certificate_delete,
        name='certificate_delete'
    ),

    path(
        'admin/resource/<int:resource_id>/edit/',
        views.course_resource_edit,
        name='course_resource_edit'
    ),

    path(
        'admin/assignment/<int:assignment_id>/edit/',
        views.assignment_edit,
        name='assignment_edit'
    ),

    path(
        'admin/assignment/<int:assignment_id>/delete/',
        views.assignment_delete,
        name='assignment_delete'
    ),

    path(
        'admin/resource/<int:resource_id>/delete/',
        views.course_resource_delete,
        name='course_resource_delete'
    ),

    # =====================================================
    # STUDENT RESOURCES
    # =====================================================

    path(
        'admin/course/<int:course_id>/student/<int:student_id>/send/',
        views.send_student_resource,
        name='send_student_resource'
    ),
    path(
    'admin/course/<int:course_id>/student/<int:student_id>/certificate/',
    views.issue_certificate,
    name='issue_certificate'
),

    # =====================================================
    # QUESTIONS
    # =====================================================

    path(
        'admin/questions/',
        views.admin_questions,
        name='admin_questions'
    ),

    path(
        'admin/question/<int:question_id>/answer/',
        views.answer_question,
        name='answer_question'
    ),

    # =====================================================
    # STUDENT
    # =====================================================

    path(
        'student/dashboard/',
        views.student_dashboard,
        name='student_dashboard'
    ),

    # =====================================================
    # COURSE LEARNING
    # =====================================================

    path(
        'learn/<slug:slug>/',
        views.my_learning,
        name='watch_course'
    ),

    # =====================================================
    # LECTURE
    # =====================================================

    path(
        'lecture/<int:lecture_id>/ask/',
        views.ask_question,
        name='ask_question'
    ),

    path(
        'lecture/<int:lecture_id>/complete/',
        views.complete_lecture,
        name='complete_lecture'
    ),

    # =====================================================
    # ASSIGNMENT
    # =====================================================

    path(
        'assignment/<int:assignment_id>/submit/',
        views.submit_assignment,
        name='submit_assignment'
    ),

    # =====================================================
    # CERTIFICATES
    # =====================================================

    path(
        'certificates/',
        views.my_certificates,
        name='my_certificates'
    ),

    # PUBLIC CREDENTIAL VERIFICATION
    # MUST COME BEFORE <slug:slug>/

    path(
        'verify-credential/',
        views.verify_credential,
        name='verify_credential'
    ),

    # =====================================================
    # PAYMENTS
    # =====================================================

    path(
        'pay/<int:course_id>/',
        views.initiate_payment,
        name='initiate_payment'
    ),

    path(
        'pay/verify/<int:payment_id>/',
        views.verify_payment,
        name='verify_payment'
    ),

    path(
        'pay/cancelled/<int:payment_id>/',
        views.payment_cancelled,
        name='payment_cancelled'
    ),

    path(
        'payment/success/<int:payment_id>/',
        views.payment_success,
        name='payment_success'
    ),

    path(
        'payments/history/',
        views.payment_history,
        name='payment_history'
    ),
    path(
    "admin/certificates/create/",
    views.create_certificate,
    name="create_certificate"
),

    # =====================================================
    # PUBLIC COURSE DETAIL
    #
    # IMPORTANT:
    # This dynamic slug route MUST BE LAST.
    # =====================================================

    path(
        '<slug:slug>/',
        views.course_detail,
        name='course_detail'
    ),
]