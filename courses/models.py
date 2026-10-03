import uuid
from django.conf import settings
from django.db import models


class Course(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    thumbnail = models.ImageField(upload_to='course_thumbnails/', blank=True, null=True)

    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='courses',
        limit_choices_to={'role': 'admin'}
    )

    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = uuid.uuid4().hex[:8]
            self.slug = f"{self.title[:180].lower().replace(' ', '-')}-{base_slug}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def lecture_count(self):
        return self.lectures.count()

    def is_free(self):
        return self.price == 0


class Lecture(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='lectures'
    )

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    video_file = models.FileField(
        upload_to='lecture_videos/',
        help_text='Upload the recorded lecture video (mp4 recommended).'
    )

    order = models.PositiveIntegerField(default=1)
    duration_minutes = models.PositiveIntegerField(default=0, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class Enrollment(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='enrollments',
        limit_choices_to={'role': 'student'}
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )

    enrolled_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('student', 'course')
        ordering = ['-enrolled_at']

    def __str__(self):
        return f"{self.student.username} -> {self.course.title}"


class Payment(models.Model):

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    )

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payments'
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='payments'
    )

    amount = models.DecimalField(max_digits=8, decimal_places=2)
    transaction_id = models.CharField(max_length=100, unique=True)

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )

    razorpay_order_id = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    razorpay_payment_id = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    razorpay_signature = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.transaction_id} - {self.student.username} - {self.status}"


class CourseResource(models.Model):

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='resources'
    )

    title = models.CharField(max_length=200)

    resource_type = models.CharField(
        max_length=10,
        choices=(
            ('pdf', 'PDF'),
            ('ebook', 'eBook'),
            ('other', 'Other File')
        ),
        default='pdf'
    )

    file = models.FileField(upload_to='course_resources/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class StudentResource(models.Model):

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='personal_resources',
        limit_choices_to={'role': 'student'}
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='personal_resources'
    )

    title = models.CharField(max_length=200)

    file = models.FileField(
        upload_to='student_resources/'
    )

    note = models.CharField(
        max_length=255,
        blank=True
    )

    sent_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sent_resources'
    )

    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return f"{self.title} -> {self.student.username}"


class Question(models.Model):

    lecture = models.ForeignKey(
        Lecture,
        on_delete=models.CASCADE,
        related_name='questions'
    )

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='questions',
        limit_choices_to={'role': 'student'}
    )

    question_text = models.TextField()

    answer_text = models.TextField(
        blank=True,
        null=True
    )

    answered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='answered_questions'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    answered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def is_answered(self):
        return bool(self.answer_text)

    def __str__(self):
        return f"Q: {self.question_text[:40]} ({self.lecture.title})"


# ============================================================
# LECTURE PROGRESS
# ============================================================

class LectureProgress(models.Model):

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='lecture_progress',
        limit_choices_to={'role': 'student'}
    )

    lecture = models.ForeignKey(
        Lecture,
        on_delete=models.CASCADE,
        related_name='progress'
    )

    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'lecture')
        ordering = ['completed_at']

    def __str__(self):
        return f"{self.student.username} completed {self.lecture.title}"


# ============================================================
# ASSIGNMENTS
# ============================================================

class Assignment(models.Model):

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='assignments'
    )

    after_lecture = models.ForeignKey(
        Lecture,
        on_delete=models.CASCADE,
        related_name='assignments',
        help_text='This assignment appears after this lecture.'
    )

    title = models.CharField(max_length=200)

    question = models.TextField()

    correct_answer = models.TextField(
        help_text='Used for automatic checking.'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['after_lecture__order', 'created_at']

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class AssignmentSubmission(models.Model):

    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name='submissions'
    )

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='assignment_submissions',
        limit_choices_to={'role': 'student'}
    )

    answer = models.TextField()

    is_correct = models.BooleanField(default=False)

    submitted_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('assignment', 'student')
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.student.username} - {self.assignment.title}"


# ============================================================
# CERTIFICATES
# ============================================================

class Certificate(models.Model):

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='certificates',
        limit_choices_to={'role': 'student'}
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='certificates'
    )

    credential_id = models.CharField(
        max_length=80,
        unique=True
    )

    issued_at = models.DateTimeField(
        auto_now_add=True
    )

    certificate_file = models.FileField(
        upload_to='certificates/',
        blank=True,
        null=True,
        help_text='Optional PDF/image certificate uploaded by admin.'
    )

    class Meta:
        unique_together = ('student', 'course')
        ordering = ['-issued_at']

    def __str__(self):
        return f"{self.credential_id} - {self.student.username} - {self.course.title}"