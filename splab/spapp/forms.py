from django import forms
from django.contrib.auth.models import User
from django.utils.text import slugify

from .models import Course


class AdminCourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ('title', 'description', 'instructor', 'price')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['instructor'].queryset = User.objects.filter(is_staff=True).order_by('first_name', 'last_name', 'username')
        self.fields['description'].required = True

    def save(self, commit=True):
        course = super().save(commit=False)
        course.slug = self._build_unique_slug(course.title, course.pk)
        course.category = course.category or 'General'
        course.short_description = course.short_description or (course.description[:120] if course.description else 'Course overview')
        course.level = course.level or Course.Level.BEGINNER
        course.duration_weeks = course.duration_weeks or 4
        if commit:
            course.save()
        return course

    @staticmethod
    def _build_unique_slug(title, course_id=None):
        base_slug = slugify(title)[:200] or 'course'
        slug = base_slug
        counter = 1
        while Course.objects.filter(slug=slug).exclude(pk=course_id).exists():
            counter += 1
            suffix = f'-{counter}'
            slug = f'{base_slug[:220 - len(suffix)]}{suffix}'
        return slug
