from django import forms

from .models import Assignment, Course, Lesson, Submission, Tutor


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'description', 'thumbnail', 'category', 'price', 'is_published']


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['course', 'title', 'content', 'video_url', 'attachments']


class AssignmentForm(forms.ModelForm):
    due_date = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}))

    class Meta:
        model = Assignment
        fields = ['course', 'title', 'description', 'due_date']


class TutorProfileForm(forms.ModelForm):
    class Meta:
        model = Tutor
        fields = ['bio', 'profile_picture', 'experience_years', 'specialization']


class SubmissionGradeForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['grade']
