from django.contrib import admin
from .models import (
    Course,
    Lecture,
    Enrollment,
    Payment,
    CourseResource,
    StudentResource,
    Question,
    Assignment,
    AssignmentSubmission,
    LectureProgress,
    Certificate,
)

class LectureInline(admin.TabularInline):
    model = Lecture
    extra = 1


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'instructor', 'price', 'is_published', 'created_at')
    list_filter = ('is_published',)
    search_fields = ('title',)
    inlines = [LectureInline]


@admin.register(Lecture)
class LectureAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order', 'duration_minutes')


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'enrolled_at', 'is_active')
    list_filter = ('is_active',)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'student', 'course', 'amount', 'status', 'created_at')
    list_filter = ('status',)


@admin.register(CourseResource)
class CourseResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'resource_type', 'uploaded_at')
    list_filter = ('resource_type',)


@admin.register(StudentResource)
class StudentResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'student', 'course', 'sent_by', 'sent_at')


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('lecture', 'student', 'is_answered', 'created_at')
    list_filter = ('lecture__course',)

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):

    list_display = (
        'title',
        'course',
        'after_lecture',
        'created_at'
    )

    list_filter = (
        'course',
    )


@admin.register(AssignmentSubmission)
class AssignmentSubmissionAdmin(admin.ModelAdmin):

    list_display = (
        'assignment',
        'student',
        'is_correct',
        'submitted_at'
    )

    list_filter = (
        'is_correct',
    )


@admin.register(LectureProgress)
class LectureProgressAdmin(admin.ModelAdmin):

    list_display = (
        'student',
        'lecture',
        'completed_at'
    )


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):

    list_display = (
        'credential_id',
        'student',
        'course',
        'issued_at'
    )

    search_fields = (
        'credential_id',
        'student__username',
        'course__title'
    )