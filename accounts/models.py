from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model.
    role = 'admin'   -> can create courses & upload lectures (also set is_staff=True)
    role = 'student' -> can browse courses, pay, and watch enrolled lectures
    """
    ROLE_CHOICES = (
        ('admin', 'Admin / Instructor'),
        ('student', 'Student'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    phone = models.CharField(max_length=15, blank=True, null=True)

    def is_admin_role(self):
        return self.role == 'admin' or self.is_superuser

    def __str__(self):
        return f"{self.username} ({self.role})"
