import uuid

import razorpay
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.db.models import Sum

from .decorators import admin_required, student_required
from .forms import CourseForm, LectureForm
from .models import Course, Lecture, Enrollment, Payment

razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


# ---------------------------------------------------------------------------
# Public pages
# ---------------------------------------------------------------------------

def home(request):
    courses = Course.objects.filter(is_published=True)
    return render(request, 'home.html', {'courses': courses})


def course_detail(request, slug):
    course = get_object_or_404(Course, slug=slug, is_published=True)
    is_enrolled = False
    if request.user.is_authenticated and request.user.role == 'student':
        is_enrolled = Enrollment.objects.filter(
            student=request.user, course=course, is_active=True
        ).exists()
    lectures = course.lectures.all()
    return render(request, 'courses/course_detail.html', {
        'course': course,
        'lectures': lectures,
        'is_enrolled': is_enrolled,
    })


# ---------------------------------------------------------------------------
# ADMIN side: create courses, upload recorded lectures, view sales
# ---------------------------------------------------------------------------

@admin_required
def admin_dashboard(request):
    courses = Course.objects.filter(instructor=request.user)
    total_students = Enrollment.objects.filter(course__instructor=request.user, is_active=True).count()
    total_revenue = Payment.objects.filter(
        course__instructor=request.user, status='success'
    ).aggregate(total=Sum('amount'))['total'] or 0
    return render(request, 'courses/dashboard_admin.html', {
        'courses': courses,
        'total_students': total_students,
        'total_revenue': total_revenue,
    })


@admin_required
def course_create(request):
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save(commit=False)
            course.instructor = request.user
            course.save()
            messages.success(request, f'Course "{course.title}" created! Now add lectures to it.')
            return redirect('lecture_create', course_id=course.id)
    else:
        form = CourseForm()
    return render(request, 'courses/course_form.html', {'form': form, 'action': 'Create'})


@admin_required
def course_edit(request, course_id):
    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, 'Course updated successfully.')
            return redirect('admin_dashboard')
    else:
        form = CourseForm(instance=course)
    return render(request, 'courses/course_form.html', {'form': form, 'action': 'Edit', 'course': course})


@admin_required
def course_delete(request, course_id):
    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    if request.method == 'POST':
        course.delete()
        messages.success(request, 'Course deleted.')
        return redirect('admin_dashboard')
    return render(request, 'courses/confirm_delete.html', {'object': course, 'type': 'course'})


@admin_required
def lecture_create(request, course_id):
    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    if request.method == 'POST':
        form = LectureForm(request.POST, request.FILES)
        if form.is_valid():
            lecture = form.save(commit=False)
            lecture.course = course
            lecture.save()
            messages.success(request, f'Lecture "{lecture.title}" uploaded to {course.title}.')
            return redirect('lecture_create', course_id=course.id)
    else:
        next_order = course.lectures.count() + 1
        form = LectureForm(initial={'order': next_order})
    lectures = course.lectures.all()
    return render(request, 'courses/lecture_form.html', {
        'form': form, 'course': course, 'lectures': lectures,
    })


@admin_required
def lecture_delete(request, lecture_id):
    lecture = get_object_or_404(Lecture, id=lecture_id, course__instructor=request.user)
    course_id = lecture.course.id
    if request.method == 'POST':
        lecture.delete()
        messages.success(request, 'Lecture deleted.')
        return redirect('lecture_create', course_id=course_id)
    return render(request, 'courses/confirm_delete.html', {'object': lecture, 'type': 'lecture'})


@admin_required
def admin_course_students(request, course_id):
    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    enrollments = Enrollment.objects.filter(course=course, is_active=True).select_related('student')
    return render(request, 'courses/admin_course_students.html', {
        'course': course, 'enrollments': enrollments,
    })


# ---------------------------------------------------------------------------
# STUDENT side: browse, dashboard, my learning
# ---------------------------------------------------------------------------

@student_required
def student_dashboard(request):
    enrollments = Enrollment.objects.filter(student=request.user, is_active=True).select_related('course')
    available_courses = Course.objects.filter(is_published=True).exclude(
        id__in=enrollments.values_list('course_id', flat=True)
    )
    return render(request, 'courses/dashboard_student.html', {
        'enrollments': enrollments,
        'available_courses': available_courses,
    })


@student_required
def my_learning(request, slug):
    """
    Watch page for an ENROLLED course. Locked if not enrolled / not paid.
    """
    course = get_object_or_404(Course, slug=slug)
    enrolled = Enrollment.objects.filter(student=request.user, course=course, is_active=True).exists()
    if not enrolled and not course.is_free():
        messages.warning(request, 'You need to purchase this course before you can watch the lectures.')
        return redirect('initiate_payment', course_id=course.id)
    if not enrolled and course.is_free():
        Enrollment.objects.get_or_create(student=request.user, course=course)
    lectures = course.lectures.all()
    return render(request, 'courses/watch_course.html', {'course': course, 'lectures': lectures})


# ---------------------------------------------------------------------------
# PAYMENT FLOW — RAZORPAY (UPI only, fully automatic)
# ---------------------------------------------------------------------------

@student_required
def initiate_payment(request, course_id):
    """
    Creates a real Razorpay Order and renders the checkout page
    (configured to show ONLY the UPI payment method).
    The course stays LOCKED until verify_payment() confirms a valid,
    signed payment from Razorpay -- no manual approval needed.
    """
    course = get_object_or_404(Course, id=course_id, is_published=True)

    already_enrolled = Enrollment.objects.filter(
        student=request.user, course=course, is_active=True
    ).exists()
    if already_enrolled:
        messages.info(request, 'You are already enrolled in this course.')
        return redirect('watch_course', slug=course.slug)

    if course.is_free():
        Enrollment.objects.get_or_create(student=request.user, course=course)
        messages.success(request, f'Enrolled in "{course.title}" for free!')
        return redirect('watch_course', slug=course.slug)

    amount_in_paise = int(course.price * 100)
    receipt = f"ucy_{course.id}_{request.user.id}_{uuid.uuid4().hex[:8]}"

    # Create the order on Razorpay's servers
    razorpay_order = razorpay_client.order.create({
        'amount': amount_in_paise,
        'currency': 'INR',
        'receipt': receipt,
        'payment_capture': 1,  # auto-capture the payment
    })

    # Save a local PENDING payment record linked to this Razorpay order.
    # Course access is granted ONLY when verify_payment() marks this success.
    payment, _ = Payment.objects.update_or_create(
        student=request.user, course=course, status='pending',
        defaults={
            'amount': course.price,
            'transaction_id': receipt,
            'razorpay_order_id': razorpay_order['id'],
        }
    )

    context = {
        'course': course,
        'payment': payment,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'razorpay_order_id': razorpay_order['id'],
        'amount_in_paise': amount_in_paise,
        'student_name': request.user.username,
        'student_email': request.user.email,
    }
    return render(request, 'courses/payment.html', context)


@student_required
def verify_payment(request, payment_id):
    """
    Called via JS (fetch/AJAX) from the Razorpay Checkout success handler.
    Verifies the cryptographic signature Razorpay sends back -- this is
    what proves the payment is genuine and wasn't faked from the browser.
    Only after this succeeds does the Enrollment get created — the course
    unlocks IMMEDIATELY, no waiting, no admin approval.
    """
    payment = get_object_or_404(Payment, id=payment_id, student=request.user, status='pending')

    razorpay_payment_id = request.POST.get('razorpay_payment_id', '')
    razorpay_order_id = request.POST.get('razorpay_order_id', '')
    razorpay_signature = request.POST.get('razorpay_signature', '')

    params_dict = {
        'razorpay_order_id': razorpay_order_id,
        'razorpay_payment_id': razorpay_payment_id,
        'razorpay_signature': razorpay_signature,
    }

    try:
        razorpay_client.utility.verify_payment_signature(params_dict)
    except razorpay.errors.SignatureVerificationError:
        payment.status = 'failed'
        payment.save()
        return JsonResponse({'status': 'failed', 'message': 'Signature verification failed.'}, status=400)

    # Signature valid -> payment is genuine -> unlock instantly
    payment.status = 'success'
    payment.razorpay_payment_id = razorpay_payment_id
    payment.razorpay_signature = razorpay_signature
    payment.save()

    Enrollment.objects.get_or_create(student=request.user, course=payment.course, defaults={'is_active': True})

    return JsonResponse({
        'status': 'success',
        'redirect_url': reverse('payment_success', args=[payment.id]),
    })


@student_required
def payment_cancelled(request, payment_id):
    """User closed the Razorpay checkout modal without paying."""
    payment = get_object_or_404(Payment, id=payment_id, student=request.user)
    if payment.status == 'pending':
        payment.status = 'failed'
        payment.save()
    messages.warning(request, 'Payment was not completed. You can try again anytime.')
    return redirect('course_detail', slug=payment.course.slug)


@student_required
def payment_success(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id, student=request.user, status='success')
    return render(request, 'courses/payment_success.html', {'payment': payment})


@student_required
def payment_history(request):
    payments = Payment.objects.filter(student=request.user)
    return render(request, 'courses/payment_history.html', {'payments': payments})
