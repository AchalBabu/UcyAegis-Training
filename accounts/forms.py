from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User


class StudentRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone = forms.CharField(required=False, max_length=15)

    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'student'
        user.email = self.cleaned_data['email']
        user.phone = self.cleaned_data.get('phone', '')
        if commit:
            user.save()
        return user


class AdminRegisterForm(UserCreationForm):
    """
    Used to create additional Admin/Instructor accounts.
    In production, only let an existing admin/superuser create new admins
    (already enforced in the view with @admin_required).
    """
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'admin'
        user.is_staff = True
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user
