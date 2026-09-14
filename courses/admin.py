from django.contrib import admin
from .models import Course, Lecture, Enrollment, Payment


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
