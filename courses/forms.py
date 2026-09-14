from django import forms
from .models import Course, Lecture


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'description', 'price', 'thumbnail', 'is_published']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
        }


class LectureForm(forms.ModelForm):
    class Meta:
        model = Lecture
        fields = ['title', 'description', 'video_file', 'order', 'duration_minutes']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
