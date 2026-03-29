from django import forms
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.text import slugify

from .models import AssignmentSubmission, Course, InstructorProfile


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


class AdminInstructorForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput, required=False)

    class Meta:
        model = InstructorProfile
        fields = ('first_name', 'last_name', 'email', 'password', 'expertise', 'experience')

    def __init__(self, *args, **kwargs):
        self.user_instance = kwargs.pop('user_instance', None)
        super().__init__(*args, **kwargs)

        if self.instance.pk:
            self.fields['password'].help_text = 'Leave blank to keep the current password.'
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        qs = User.objects.filter(email=email)
        if self.user_instance:
            qs = qs.exclude(pk=self.user_instance.pk)
        if qs.exists():
            raise forms.ValidationError('An instructor with this email already exists.')
        return email

    def save(self, commit=True):
        email = self.cleaned_data['email']
        first_name = self.cleaned_data['first_name']
        last_name = self.cleaned_data['last_name']
        password = self.cleaned_data.get('password')

        user = self.user_instance
        if user is None:
            user = User(username=email, email=email, is_staff=True)
        else:
            user.username = email
            user.email = email

        user.first_name = first_name
        user.last_name = last_name
        user.is_staff = True

        if password:
            user.set_password(password)

        if commit:
            user.save()

        profile = super().save(commit=False)
        profile.user = user

        if commit:
            profile.save()

        return profile


class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)


class RegisterForm(forms.Form):
    USER_TYPE_CHOICES = (
        ('user', 'User'),
        ('instructor', 'Instructor'),
        ('admin', 'Admin'),
    )

    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    email = forms.EmailField()
    user_type = forms.ChoiceField(choices=USER_TYPE_CHOICES)
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(username=email).exists() or User.objects.filter(email=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', 'Passwords do not match.')
        return cleaned_data


class InstructorCourseRequestForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ('title', 'category', 'short_description', 'description', 'level', 'duration_weeks', 'price')

    def save(self, commit=True):
        course = super().save(commit=False)
        course.slug = AdminCourseForm._build_unique_slug(course.title, course.pk)
        course.is_published = False
        course.approval_status = Course.ApprovalStatus.PENDING
        if commit:
            course.save()
        return course


class CourseSectionForm(forms.Form):
    section_title = forms.CharField(max_length=150)


class CourseVideoForm(forms.Form):
    section_id = forms.IntegerField(min_value=1)
    video_title = forms.CharField(max_length=180)
    video_url = forms.URLField()
    duration_minutes = forms.IntegerField(min_value=1, required=False, initial=1)


class CourseNoteForm(forms.Form):
    note_title = forms.CharField(max_length=150)
    note_content = forms.CharField(required=False, widget=forms.Textarea)
    note_file_url = forms.URLField(required=False)


class CourseAssignmentForm(forms.Form):
    test_title = forms.CharField(max_length=180)
    instructions = forms.CharField(widget=forms.Textarea)
    due_at = forms.DateTimeField(
        input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M'],
    )
    max_score = forms.IntegerField(min_value=1, required=False, initial=100)

    def clean_due_at(self):
        due_at = self.cleaned_data['due_at']
        return timezone.make_aware(due_at) if timezone.is_naive(due_at) else due_at


class TestAttemptForm(forms.ModelForm):
    answer_text = forms.CharField(required=False, widget=forms.Textarea)

    class Meta:
        model = AssignmentSubmission
        fields = ('submission_url',)

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('submission_url') and not cleaned_data.get('answer_text'):
            raise forms.ValidationError('Please provide an answer text or submission URL.')
        return cleaned_data
