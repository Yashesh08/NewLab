from django import forms

from .models import Assignment, Course, Lesson, Submission, Tutor


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'description', 'thumbnail', 'price']


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['course', 'title', 'video', 'pdf_material']


class AssignmentForm(forms.ModelForm):
    due_date = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}))

    class Meta:
        model = Assignment
        fields = ['course', 'title', 'description', 'due_date']


class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['file']


class SubmissionGradeForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['grade']


class TutorProfileForm(forms.ModelForm):
    class Meta:
        model = Tutor
        fields = ['bio', 'specialization', 'experience_years', 'profile_image', 'rating']
