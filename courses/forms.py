from django import forms
from .models import Certificate
from .models import (
    Course,
    Lecture,
    CourseResource,
    StudentResource,
    Question,
    Assignment,
    AssignmentSubmission,
    Certificate,
)


class CourseForm(forms.ModelForm):

    class Meta:
        model = Course

        fields = [
            'title',
            'description',
            'price',
            'thumbnail',
            'is_published'
        ]

        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
        }


class LectureForm(forms.ModelForm):

    class Meta:
        model = Lecture

        fields = [
            'title',
            'description',
            'video_file',
            'order',
            'duration_minutes'
        ]

        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class CourseResourceForm(forms.ModelForm):

    class Meta:
        model = CourseResource

        fields = [
            'title',
            'resource_type',
            'file'
        ]

        widgets = {
            'title': forms.TextInput(
                attrs={
                    'placeholder': 'e.g. Chapter 1 Notes.pdf'
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # When editing, uploading a new file is optional (keep the old one).
        if self.instance and self.instance.pk:
            self.fields['file'].required = False
            # plain input: no "Clear" checkbox, so the file can never be emptied
            self.fields['file'].widget = forms.FileInput()
            self.fields['file'].help_text = (
                'Leave empty to keep the current file, or choose a new one to replace it.'
            )


class StudentResourceForm(forms.ModelForm):

    class Meta:
        model = StudentResource

        fields = [
            'title',
            'file',
            'note'
        ]

        widgets = {
            'title': forms.TextInput(
                attrs={
                    'placeholder': 'e.g. Course Completion Certificate'
                }
            ),
            'note': forms.TextInput(
                attrs={
                    'placeholder': 'Optional note for the student'
                }
            ),
        }


class AssignmentForm(forms.ModelForm):

    class Meta:
        model = Assignment

        fields = [
            'after_lecture',
            'title',
            'question',
            'correct_answer'
        ]

        widgets = {

            'title': forms.TextInput(
                attrs={
                    'placeholder': 'e.g. Assignment 1'
                }
            ),

            'question': forms.Textarea(
                attrs={
                    'rows': 4,
                    'placeholder': 'Write the assignment question...'
                }
            ),

            'correct_answer': forms.Textarea(
                attrs={
                    'rows': 2,
                    'placeholder': 'Write the correct answer...'
                }
            ),
        }

    def __init__(self, *args, course=None, **kwargs):

        super().__init__(*args, **kwargs)

        if course is not None:
            self.fields[
                'after_lecture'
            ].queryset = course.lectures.all()


class AssignmentSubmissionForm(forms.ModelForm):

    class Meta:
        model = AssignmentSubmission

        fields = [
            'answer'
        ]

        widgets = {

            'answer': forms.Textarea(
                attrs={
                    'rows': 4,
                    'placeholder': 'Write your answer here...',
                    'style': (
                        'width:100%;'
                        'padding:10px;'
                        'border-radius:6px;'
                        'border:1px solid #ccc;'
                        'font-family:inherit;'
                        'font-size:14px;'
                    ),
                }
            )
        }


class QuestionForm(forms.ModelForm):

    class Meta:
        model = Question

        fields = [
            'question_text'
        ]

        widgets = {

            'question_text': forms.Textarea(
                attrs={
                    'rows': 2,
                    'placeholder': 'Ask a question about this video...',
                    'style': (
                        'width:100%;'
                        'padding:10px;'
                        'border-radius:6px;'
                        'border:1px solid #ccc;'
                    ),
                }
            ),
        }


class AnswerForm(forms.Form):

    answer_text = forms.CharField(

        widget=forms.Textarea(
            attrs={
                'rows': 2,
                'placeholder': 'Write your answer...',
                'style': (
                    'width:100%;'
                    'padding:10px;'
                    'border-radius:6px;'
                    'border:1px solid #ccc;'
                ),
            }
        )
    )


class CertificateAdminForm(forms.ModelForm):

    class Meta:
        model = Certificate
        fields = [
            "student",
            "course",
            "credential_id",
            "certificate_file",
        ]

        widgets = {
            "student": forms.Select(attrs={
                "class": "form-control"
            }),

            "course": forms.Select(attrs={
                "class": "form-control"
            }),

            "credential_id": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Example: UCY-PY-2026-00125"
            }),

            "certificate_file": forms.ClearableFileInput(attrs={
                "class": "form-control",
                "accept": "image/*,.pdf"
            }),
        }

    def clean_credential_id(self):
        credential_id = self.cleaned_data["credential_id"].strip()

        if Certificate.objects.filter(
            credential_id__iexact=credential_id
        ).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(
                "This Credential ID already exists."
            )

        return credential_id