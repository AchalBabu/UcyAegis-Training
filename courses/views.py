import uuid
from .models import Certificate
from .forms import CertificateAdminForm
from .progress import (
    progress_for_student,
    progress_for_course,
    course_overview,
    unlocked_lecture_ids,
    certificate_pending,
)
import razorpay
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.db.models import Sum

from accounts.models import User
from .decorators import admin_required, student_required
from .forms import (
    CourseForm,
    LectureForm,
    CourseResourceForm,
    StudentResourceForm,
    QuestionForm,
    AnswerForm,
    AssignmentForm,
    AssignmentSubmissionForm,
)
from .models import (
    Course,
    Lecture,
    Enrollment,
    Payment,
    CourseResource,
    StudentResource,
    Question,
    LectureProgress,
    Assignment,
    AssignmentSubmission,
    Certificate,
)

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
    lectures = list(course.lectures.all())
    preview_count = getattr(settings, 'FREE_PREVIEW_LECTURES', 2)
    if is_enrolled or course.is_free():
        unlocked_ids = {lecture.id for lecture in lectures}
    else:
        unlocked_ids = {lecture.id for lecture in lectures[:preview_count]}
    return render(request, 'courses/course_detail.html', {
        'course': course,
        'lectures': lectures,
        'is_enrolled': is_enrolled,
        'unlocked_ids': unlocked_ids,
        'preview_count': preview_count,
    })


# ---------------------------------------------------------------------------
# ADMIN side: create courses, upload recorded lectures, view sales
# ---------------------------------------------------------------------------

@admin_required
def admin_dashboard(request):
    courses = list(Course.objects.filter(instructor=request.user))
    for c in courses:
        student_ids = Enrollment.objects.filter(
            course=c, is_active=True
        ).values_list('student_id', flat=True)
        c.overview = course_overview(c, student_ids)
    total_students = Enrollment.objects.filter(course__instructor=request.user, is_active=True).count()
    overall_avg = (
        int(round(sum(c.overview['avg_percent'] * c.overview['students'] for c in courses) / total_students))
        if total_students else 0
    )
    completed_total = sum(c.overview['completed'] for c in courses)
    total_revenue = Payment.objects.filter(
        course__instructor=request.user, status='success'
    ).aggregate(total=Sum('amount'))['total'] or 0
    return render(request, 'courses/dashboard_admin.html', {
        'courses': courses,
        'total_students': total_students,
        'total_revenue': total_revenue,
        'overall_avg': overall_avg,
        'completed_total': completed_total,
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
def assignment_manage(request, course_id):

    course = get_object_or_404(
        Course,
        id=course_id,
        instructor=request.user
    )

    if request.method == 'POST':

        form = AssignmentForm(
            request.POST,
            course=course
        )

        if form.is_valid():

            assignment = form.save(
                commit=False
            )

            assignment.course = course

            assignment.save()

            messages.success(
                request,
                f'Assignment "{assignment.title}" added.'
            )

            return redirect(
                'assignment_manage',
                course_id=course.id
            )

    else:

        form = AssignmentForm(
            course=course
        )

    assignments = course.assignments.select_related(
        'after_lecture'
    ).all()

    return render(
        request,
        'courses/assignment_manage.html',
        {
            'course': course,
            'form': form,
            'assignments': assignments,
        }
    )

def _delete_file(field_file):
    """Remove an uploaded file from disk (ignore if it is already gone)."""
    try:
        if field_file and field_file.name:
            field_file.delete(save=False)
    except Exception:
        pass


@admin_required
def assignment_edit(request, assignment_id):
    assignment = get_object_or_404(
        Assignment, id=assignment_id, course__instructor=request.user
    )
    course = assignment.course

    if request.method == 'POST':
        form = AssignmentForm(request.POST, instance=assignment, course=course)
        if form.is_valid():
            assignment = form.save()

            # The correct answer may have changed -> re-grade old submissions
            # so students are never stuck with a stale pass/fail result.
            new_answer = assignment.correct_answer.strip().casefold()
            regraded = 0
            for sub in assignment.submissions.all():
                is_ok = sub.answer.strip().casefold() == new_answer
                if sub.is_correct != is_ok:
                    sub.is_correct = is_ok
                    sub.save(update_fields=['is_correct'])
                    regraded += 1

            msg = f'Assignment "{assignment.title}" updated.'
            if regraded:
                msg += f' {regraded} student submission(s) were re-checked.'
            messages.success(request, msg)
            return redirect('assignment_manage', course_id=course.id)
    else:
        form = AssignmentForm(instance=assignment, course=course)

    return render(request, 'courses/assignment_edit.html', {
        'form': form, 'course': course, 'assignment': assignment,
    })


@admin_required
def assignment_delete(request, assignment_id):
    assignment = get_object_or_404(
        Assignment, id=assignment_id, course__instructor=request.user
    )
    course = assignment.course

    if request.method == 'POST':
        title = assignment.title
        assignment.delete()
        messages.success(request, f'Assignment "{title}" deleted.')
        return redirect('assignment_manage', course_id=course.id)

    count = assignment.submissions.count()
    return render(request, 'courses/confirm_delete.html', {
        'object': assignment,
        'type': 'assignment',
        'warning': (
            f'{count} student submission(s) will also be removed. '
            'Students will no longer need to pass it to unlock the next lecture.'
            if count else
            'Students will no longer need to pass it to unlock the next lecture.'
        ),
        'back_url': reverse('assignment_manage', args=[course.id]),
    })


@admin_required
def admin_course_students(request, course_id):
    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    enrollments = list(
        Enrollment.objects.filter(course=course, is_active=True).select_related('student')
    )
    overview = course_overview(course, [e.student_id for e in enrollments])
    certified_ids = set(
        Certificate.objects.filter(course=course).values_list('student_id', flat=True)
    )
    pending = 0
    for e in enrollments:
        e.progress = overview['per_student'][e.student_id]
        e.has_certificate = e.student_id in certified_ids
        e.certificate_pending = (
            e.progress.status == 'completed' and not e.has_certificate
        )
        pending += 1 if e.certificate_pending else 0
    overview['certificates_pending'] = pending
    return render(request, 'courses/admin_course_students.html', {
        'course': course, 'enrollments': enrollments, 'overview': overview,
    })


@admin_required
def admin_student_progress(request, course_id, student_id):
    """Admin: lecture-by-lecture / assignment-by-assignment view of ONE student."""
    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    student = get_object_or_404(User, id=student_id, role='student')
    enrollment = get_object_or_404(Enrollment, student=student, course=course, is_active=True)

    lectures = list(course.lectures.all())
    done = {
        lp.lecture_id: lp.completed_at
        for lp in LectureProgress.objects.filter(student=student, lecture__course=course)
    }
    submissions = {
        sub.assignment_id: sub
        for sub in AssignmentSubmission.objects.filter(student=student, assignment__course=course)
    }
    assignments_by_lecture = {}
    for a in course.assignments.all():
        assignments_by_lecture.setdefault(a.after_lecture_id, []).append(a)

    rows = []
    for lecture in lectures:
        rows.append({
            'lecture': lecture,
            'completed_at': done.get(lecture.id),
            'assignments': [
                {'assignment': a, 'submission': submissions.get(a.id)}
                for a in assignments_by_lecture.get(lecture.id, [])
            ],
        })

    progress = progress_for_course(course, [student.id])[student.id]
    certificate = Certificate.objects.filter(student=student, course=course).first()
    return render(request, 'courses/admin_student_progress.html', {
        'course': course, 'student': student, 'enrollment': enrollment,
        'rows': rows, 'progress': progress, 'certificate': certificate,
    })


# ---------------------------------------------------------------------------
# COURSE RESOURCES — PDFs / eBooks visible to every SUBSCRIBED student
# ---------------------------------------------------------------------------

@admin_required
def course_resources(request, course_id):
    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    if request.method == 'POST':
        form = CourseResourceForm(request.POST, request.FILES)
        if form.is_valid():
            resource = form.save(commit=False)
            resource.course = course
            resource.save()
            messages.success(request, f'"{resource.title}" added to course resources.')
            return redirect('course_resources', course_id=course.id)
    else:
        form = CourseResourceForm()
    resources = course.resources.all()
    return render(request, 'courses/course_resources.html', {
        'form': form, 'course': course, 'resources': resources,
    })


@admin_required
def course_resource_edit(request, resource_id):
    resource = get_object_or_404(
        CourseResource, id=resource_id, course__instructor=request.user
    )
    course = resource.course

    if request.method == 'POST':
        old_file = resource.file          # remember the current file
        old_name = old_file.name if old_file else ''
        form = CourseResourceForm(request.POST, request.FILES, instance=resource)
        if form.is_valid():
            updated = form.save()
            # new file uploaded -> remove the previous one from disk
            if 'file' in form.changed_data and old_name and old_name != updated.file.name:
                try:
                    updated.file.storage.delete(old_name)
                except Exception:
                    pass
            messages.success(request, f'"{updated.title}" updated.')
            return redirect('course_resources', course_id=course.id)
    else:
        form = CourseResourceForm(instance=resource)

    return render(request, 'courses/resource_edit.html', {
        'form': form, 'course': course, 'resource': resource,
    })


@admin_required
def course_resource_delete(request, resource_id):
    resource = get_object_or_404(CourseResource, id=resource_id, course__instructor=request.user)
    course_id = resource.course.id
    if request.method == 'POST':
        title = resource.title
        _delete_file(resource.file)
        resource.delete()
        messages.success(request, f'"{title}" deleted.')
        return redirect('course_resources', course_id=course_id)
    return render(request, 'courses/confirm_delete.html', {
        'object': resource,
        'type': 'resource',
        'warning': 'The file will be removed for every enrolled student.',
        'back_url': reverse('course_resources', args=[course_id]),
    })


# ---------------------------------------------------------------------------
# PERSONAL RESOURCES — send a file (certificate etc.) to ONE specific student
# ---------------------------------------------------------------------------

@admin_required
def send_student_resource(request, course_id, student_id):
    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    student = get_object_or_404(User, id=student_id, role='student')
    # Safety check: only lets the admin send files to students enrolled in their own course
    get_object_or_404(Enrollment, student=student, course=course, is_active=True)

    if request.method == 'POST':
        form = StudentResourceForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.student = student
            item.course = course
            item.sent_by = request.user
            item.save()
            messages.success(request, f'"{item.title}" sent to {student.username}.')
            return redirect('admin_course_students', course_id=course.id)
    else:
        form = StudentResourceForm()
    return render(request, 'courses/send_resource.html', {
        'form': form, 'course': course, 'student': student,
    })

@admin_required
def issue_certificate(request, course_id, student_id):

    course = get_object_or_404(
        Course,
        id=course_id,
        instructor=request.user
    )

    student = get_object_or_404(
        User,
        id=student_id,
        role='student'
    )

    # Student must be enrolled in this course
    get_object_or_404(
        Enrollment,
        student=student,
        course=course,
        is_active=True
    )

    # Check if certificate already exists
    existing_certificate = Certificate.objects.filter(
        student=student,
        course=course
    ).first()

    if request.method == 'POST':

        data = request.POST.copy()
        data['student'] = student.id
        data['course'] = course.id

        form = CertificateAdminForm(
            data,
            request.FILES,
            instance=existing_certificate
        )

        if form.is_valid():

            certificate = form.save(commit=False)

            # Force correct student and course
            certificate.student = student
            certificate.course = course

            certificate.save()

            messages.success(
                request,
                f'Certificate saved for {student.username}.'
            )

            return redirect(
                'admin_course_students',
                course_id=course.id
            )

    else:

        form = CertificateAdminForm(
            instance=existing_certificate,
            initial={
                'student': student,
                'course': course,
            }
        )

    return render(
        request,
        'courses/issue_certificate.html',
        {
            'form': form,
            'course': course,
            'student': student,
            'existing_certificate': existing_certificate,
        }
    )
# ---------------------------------------------------------------------------
# VIDEO Q&A — students ask questions on a lecture, admin answers
# ---------------------------------------------------------------------------

@admin_required
def admin_questions(request):
    questions = Question.objects.filter(
        lecture__course__instructor=request.user
    ).select_related('student', 'lecture', 'lecture__course')
    answer_form = AnswerForm()
    return render(request, 'courses/admin_questions.html', {
        'questions': questions, 'answer_form': answer_form,
    })


@admin_required
def answer_question(request, question_id):
    question = get_object_or_404(Question, id=question_id, lecture__course__instructor=request.user)
    if request.method == 'POST':
        form = AnswerForm(request.POST)
        if form.is_valid():
            question.answer_text = form.cleaned_data['answer_text']
            question.answered_by = request.user
            question.answered_at = timezone.now()
            question.save()
            messages.success(request, 'Answer posted.')
    return redirect('admin_questions')


# ---------------------------------------------------------------------------
# STUDENT side: browse, dashboard, my learning
# ---------------------------------------------------------------------------

@student_required
def student_dashboard(request):

    enrollments = Enrollment.objects.filter(
        student=request.user,
        is_active=True
    ).select_related('course')

    available_courses = Course.objects.filter(
        is_published=True
    ).exclude(
        id__in=enrollments.values_list('course_id', flat=True)
    )

    course_ids = enrollments.values_list(
        'course_id',
        flat=True
    )

    course_resources = CourseResource.objects.filter(
        course_id__in=course_ids
    ).select_related('course')

    certificates = Certificate.objects.filter(
        student=request.user
    ).select_related('course')

    enrollments = list(enrollments)
    progress_map = progress_for_student(
        request.user, [e.course for e in enrollments]
    )
    certified_course_ids = {c.course_id for c in certificates}
    for e in enrollments:
        e.progress = progress_map[e.course_id]
        e.certificate_ready = e.course_id in certified_course_ids
        e.certificate_waiting = (
            e.progress.status == 'completed' and not e.certificate_ready
        )

    total_done = sum(e.progress.done_lectures for e in enrollments)
    completed_courses = sum(1 for e in enrollments if e.progress.status == 'completed')
    avg_percent = (
        int(round(sum(e.progress.percent for e in enrollments) / len(enrollments)))
        if enrollments else 0
    )
    # The course the student should jump back into
    resume = next(
        (e for e in enrollments if e.progress.status == 'in_progress'),
        next((e for e in enrollments if e.progress.status == 'not_started'), None),
    )

    return render(
        request,
        'courses/dashboard_student.html',
        {
            'enrollments': enrollments,
            'available_courses': available_courses,
            'course_resources': course_resources,
            'certificates': certificates,
            'total_done_lectures': total_done,
            'completed_courses': completed_courses,
            'avg_percent': avg_percent,
            'resume': resume,
        }
    )


@student_required
def my_learning(request, slug):

    course = get_object_or_404(
        Course,
        slug=slug,
        is_published=True
    )

    enrollment = Enrollment.objects.filter(
        student=request.user,
        course=course,
        is_active=True
    ).first()

    enrolled = bool(enrollment)

    if not enrolled and course.is_free():

        enrollment, _ = Enrollment.objects.get_or_create(
            student=request.user,
            course=course,
            defaults={
                'is_active': True
            }
        )

        enrolled = True

    lectures = list(
        course.lectures.all()
    )

    preview_count = getattr(
        settings,
        'FREE_PREVIEW_LECTURES',
        2
    )

    completed_ids = set(
        LectureProgress.objects.filter(
            student=request.user,
            lecture__course=course
        ).values_list(
            'lecture_id',
            flat=True
        )
    )

    submissions = {
        s.assignment_id: s
        for s in AssignmentSubmission.objects.filter(
            student=request.user,
            assignment__course=course
        )
    }

    all_assignments = list(
        course.assignments.select_related('after_lecture').all()
    )

    assignments_by_lecture = {}

    for assignment in all_assignments:

        assignments_by_lecture.setdefault(
            assignment.after_lecture_id,
            []
        ).append(assignment)

    passed_ids = {
        a_id
        for a_id, sub in submissions.items()
        if sub.is_correct
    }

    unlocked_ids = set()

    if enrolled:

        unlocked_ids = unlocked_lecture_ids(
            lectures,
            completed_ids,
            assignments_by_lecture,
            passed_ids
        )

    else:

        unlocked_ids = {
            lecture.id
            for lecture in lectures[:preview_count]
        }

    resources = (
        course.resources.all()
        if enrolled
        else CourseResource.objects.none()
    )

    questions_by_lecture = {}

    qs = Question.objects.filter(
        lecture__course=course
    ).select_related(
        'student',
        'lecture'
    )

    for q in qs:

        questions_by_lecture.setdefault(
            q.lecture_id,
            []
        ).append(q)

    certificate = Certificate.objects.filter(
        student=request.user,
        course=course
    ).first()

    # The certificate is issued MANUALLY by the admin (normally within 2 hours
    # of completion). Until then the student sees a "pending" message.

    progress = progress_for_student(
        request.user, [course]
    )[course.id]

    # Next thing the student should do
    next_lecture = next(
        (
            l for l in lectures
            if l.id in unlocked_ids
            and (
                l.id not in completed_ids
                or any(
                    a.id not in passed_ids
                    for a in assignments_by_lecture.get(l.id, [])
                )
            )
        ),
        None
    ) if enrolled else None

    return render(
        request,
        'courses/watch_course.html',
        {
            'course': course,
            'lectures': lectures,
            'enrolled': enrolled,
            'unlocked_ids': unlocked_ids,
            'completed_ids': completed_ids,
            'locked_count':
                len(lectures) - len(unlocked_ids),
            'preview_count': preview_count,
            'resources': resources,
            'question_form': QuestionForm(),
            'questions_by_lecture':
                questions_by_lecture,
            'assignments_by_lecture':
                assignments_by_lecture,
            'assignment_form':
                AssignmentSubmissionForm(),
            'submissions':
                submissions,
            'certificate':
                certificate,
            'progress':
                progress,
            'next_lecture':
                next_lecture,
            'passed_ids':
                passed_ids,
        }
    )

@student_required
def complete_lecture(request, lecture_id):

    lecture = get_object_or_404(
        Lecture,
        id=lecture_id
    )

    course = lecture.course

    if request.method != 'POST':
        return redirect(
            'watch_course',
            slug=course.slug
        )

    enrolled = Enrollment.objects.filter(
        student=request.user,
        course=course,
        is_active=True
    ).exists()

    if not enrolled and not course.is_free():

        messages.error(
            request,
            'Enroll in the course to track lecture progress.'
        )

        return redirect(
            'watch_course',
            slug=course.slug
        )

    if not enrolled and course.is_free():

        Enrollment.objects.get_or_create(
            student=request.user,
            course=course
        )

    lectures = list(
        course.lectures.all()
    )

    position = lectures.index(
        lecture
    )

    # Previous lecture complete hona chahiye
    if position > 0:

        previous = lectures[position - 1]

        if not LectureProgress.objects.filter(
            student=request.user,
            lecture=previous
        ).exists():

            messages.error(
                request,
                'Complete the previous lecture first.'
            )

            return redirect(
                'watch_course',
                slug=course.slug
            )

        previous_assignment = Assignment.objects.filter(
            after_lecture=previous
        ).first()

        if previous_assignment:

            submission = AssignmentSubmission.objects.filter(
                student=request.user,
                assignment=previous_assignment
            ).first()

            if not submission or not submission.is_correct:

                messages.error(
                    request,
                    'Pass the assignment before moving to the next lecture.'
                )

                return redirect(
                    'watch_course',
                    slug=course.slug
                )

    LectureProgress.objects.get_or_create(
        student=request.user,
        lecture=lecture
    )

    messages.success(
        request,
        f'"{lecture.title}" marked as complete.'
    )

    if certificate_pending(request.user, course):
        messages.success(
            request,
            '🎉 Congratulations! You have completed the course. '
            'Your certificate will be available within 2 hours.'
        )

    return redirect(
        f"{reverse('watch_course', args=[course.slug])}"
        f"#lecture-{lecture.id}"
    )

@student_required
def submit_assignment(request, assignment_id):

    assignment = get_object_or_404(
        Assignment.objects.select_related(
            'course',
            'after_lecture'
        ),
        id=assignment_id
    )

    course = assignment.course

    if not Enrollment.objects.filter(
        student=request.user,
        course=course,
        is_active=True
    ).exists():

        messages.error(
            request,
            'Enroll in the course first.'
        )

        return redirect(
            'watch_course',
            slug=course.slug
        )

    if not LectureProgress.objects.filter(
        student=request.user,
        lecture=assignment.after_lecture
    ).exists():

        messages.error(
            request,
            'Complete the lecture before attempting this assignment.'
        )

        return redirect(
            'watch_course',
            slug=course.slug
        )

    if request.method == 'POST':

        form = AssignmentSubmissionForm(
            request.POST
        )

        if form.is_valid():

            answer = form.cleaned_data[
                'answer'
            ].strip()

            correct = (
                answer.casefold()
                ==
                assignment.correct_answer.strip().casefold()
            )

            AssignmentSubmission.objects.update_or_create(

                assignment=assignment,

                student=request.user,

                defaults={
                    'answer': answer,
                    'is_correct': correct
                }
            )

            if correct:

                messages.success(
                    request,
                    'Correct! The next lecture is now unlocked.'
                )

                if certificate_pending(request.user, course):
                    messages.success(
                        request,
                        '🎉 Congratulations! You have completed the course. '
                        'Your certificate will be available within 2 hours.'
                    )

            else:

                messages.error(
                    request,
                    'Not correct yet. Please review the lecture and try again.'
                )

    return redirect(
        f"{reverse('watch_course', args=[course.slug])}"
        f"#assignment-{assignment.id}"
    )


@student_required
def ask_question(request, lecture_id):
    """Student posts a question on a lecture they currently have access to
    (either subscribed, or it's within the free preview)."""
    lecture = get_object_or_404(Lecture, id=lecture_id)
    course = lecture.course
    enrolled = Enrollment.objects.filter(student=request.user, course=course, is_active=True).exists()
    preview_count = getattr(settings, 'FREE_PREVIEW_LECTURES', 2)
    lectures = list(course.lectures.all())
    unlocked_ids = {l.id for l in lectures} if enrolled else {l.id for l in lectures[:preview_count]}

    if lecture.id not in unlocked_ids:
        messages.error(request, 'Unlock this lecture (subscribe to the course) to ask a question.')
        return redirect('watch_course', slug=course.slug)

    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.lecture = lecture
            question.student = request.user
            question.save()
            messages.success(request, 'Your question has been posted.')
    return redirect(f"{reverse('watch_course', args=[course.slug])}#lecture-{lecture.id}")


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


@student_required
def my_certificates(request):

    certificates = Certificate.objects.filter(
        student=request.user
    ).select_related('course')

    certified_ids = {c.course_id for c in certificates}
    enrollments = list(
        Enrollment.objects.filter(
            student=request.user, is_active=True
        ).select_related('course')
    )
    progress_map = progress_for_student(
        request.user, [e.course for e in enrollments]
    )
    pending_courses = [
        e.course for e in enrollments
        if progress_map[e.course_id].status == 'completed'
        and e.course_id not in certified_ids
    ]

    return render(
        request,
        'courses/my_certificates.html',
        {
            'certificates': certificates,
            'pending_courses': pending_courses,
        }
    )


def verify_credential(request):
    credential_id = request.GET.get("credential", "").strip()

    certificate = None

    if credential_id:
        certificate = (
            Certificate.objects
            .filter(credential_id__iexact=credential_id)
            .select_related("student", "course")
            .first()
        )

    return render(
        request,
        "courses/verify_credential.html",
        {
            "certificate": certificate,
            "credential_id": credential_id,
        }
    )
@admin_required
def create_certificate(request):

    if request.method == "POST":
        form = CertificateAdminForm(request.POST, request.FILES)

        if form.is_valid():
            certificate = form.save()

            messages.success(
                request,
                f"Certificate created successfully. "
                f"Credential ID: {certificate.credential_id}"
            )

            return redirect("create_certificate")

    else:
        form = CertificateAdminForm()

    certificates = Certificate.objects.select_related(
        "student",
        "course"
    ).order_by("-issued_at")

    return render(
        request,
        "courses/create_certificate.html",
        {
            "form": form,
            "certificates": certificates,
        }
    )


@admin_required
def certificate_delete(request, certificate_id):
    """Admin: delete an already issued certificate (and its uploaded file)."""
    certificate = get_object_or_404(
        Certificate.objects.select_related('student', 'course'),
        id=certificate_id,
        course__instructor=request.user,
    )
    course = certificate.course

    if request.GET.get('from') == 'students' or request.POST.get('from') == 'students':
        back_url = reverse('admin_course_students', args=[course.id])
        origin = 'students'
    else:
        back_url = reverse('create_certificate')
        origin = ''

    if request.method == 'POST':
        label = f'{certificate.credential_id} ({certificate.student.username})'
        _delete_file(certificate.certificate_file)
        certificate.delete()
        messages.success(request, f'Certificate {label} deleted.')
        return redirect(back_url)

    return render(request, 'courses/confirm_delete.html', {
        'object': f'{certificate.credential_id} — {certificate.student.username} — {course.title}',
        'type': 'certificate',
        'warning': (
            'The student will lose this certificate and it will no longer pass '
            '"Verify Certificate". You can issue a new one later.'
        ),
        'back_url': back_url,
        'hidden_from': origin,
    })
