from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.role == 'admin' or request.user.is_superuser):
            messages.error(request, 'You must be logged in as an Admin to access this page.')
            return redirect('admin_login')
        return view_func(request, *args, **kwargs)
    return wrapper


def student_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'student':
            messages.error(request, 'You must be logged in as a Student to access this page.')
            return redirect('student_login')
        return view_func(request, *args, **kwargs)
    return wrapper
