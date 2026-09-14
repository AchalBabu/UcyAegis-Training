from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from .forms import StudentRegisterForm, AdminRegisterForm
from .models import User


def student_register(request):
    if request.method == 'POST':
        form = StudentRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully! Welcome to Ucyaegis Training.')
            return redirect('student_dashboard')
    else:
        form = StudentRegisterForm()
    return render(request, 'accounts/register_student.html', {'form': form})


def student_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None and user.role == 'student':
            login(request, user)
            return redirect('student_dashboard')
        messages.error(request, 'Invalid student credentials.')
    return render(request, 'accounts/login_student.html')


def admin_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None and (user.role == 'admin' or user.is_superuser):
            login(request, user)
            return redirect('admin_dashboard')
        messages.error(request, 'Invalid admin credentials.')
    return render(request, 'accounts/login_admin.html')


def admin_register(request):
    """
    ONE-TIME bootstrap page to create THE ONLY admin account for this site.
    This URL is intentionally not linked anywhere in the UI (no nav link,
    no homepage button) -- only someone who knows the exact URL can even
    reach this page.

    Once a single admin/superuser already exists, this view permanently
    locks itself: nobody else -- even if they find this URL -- can create
    a second admin account.
    """
    admin_already_exists = User.objects.filter(role='admin').exists() or User.objects.filter(is_superuser=True).exists()

    if admin_already_exists:
        messages.error(request, 'Admin registration is closed. Only one admin account is allowed for this site.')
        return redirect('home')

    if request.method == 'POST':
        form = AdminRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Admin account created successfully! This registration page is now locked for everyone else.')
            return redirect('admin_dashboard')
    else:
        form = AdminRegisterForm()
    return render(request, 'accounts/register_admin.html', {'form': form})


@login_required
def user_logout(request):
    logout(request)
    return redirect('home')


@login_required
def delete_account(request):
    """
    Lets a STUDENT permanently delete their own account.
    Deleting the user also cascades and removes their Enrollments and
    Payment records (see courses/models.py -> on_delete=models.CASCADE).
    """
    if request.user.role != 'student':
        messages.error(request, 'Only student accounts can be deleted from here.')
        return redirect('home')

    if request.method == 'POST':
        user = request.user
        logout(request)
        user.delete()
        messages.success(request, 'Your account and all related data have been permanently deleted.')
        return redirect('home')

    return render(request, 'accounts/confirm_delete_account.html')
