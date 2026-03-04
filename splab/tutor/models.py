from django.conf import settings
from django.core.validators import FileExtensionValidator, MaxValueValidator, MinValueValidator
from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Tutor(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tutor_profiles')
    bio = models.TextField(blank=True)
    specialization = models.CharField(max_length=120, blank=True)
    experience_years = models.PositiveIntegerField(default=0)
    profile_image = models.ImageField(
        upload_to='tutor/profile/',
        blank=True,
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp'])],
    )
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user',)

    def __str__(self):
        return self.user.get_full_name() or self.user.username


class Course(TimeStampedModel):
    title = models.CharField(max_length=200)
    description = models.TextField()
    tutor = models.ForeignKey(Tutor, on_delete=models.CASCADE, related_name='courses')
    thumbnail = models.ImageField(
        upload_to='tutor/course_thumbnails/',
        blank=True,
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp'])],
    )
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    def __str__(self):
        return self.title


class Enrollment(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        COMPLETED = 'completed', 'Completed'
        PAUSED = 'paused', 'Paused'

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tutor_enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    progress = models.PositiveSmallIntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'course')


class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=180)
    video_url = models.URLField(blank=True)
    content = models.TextField(blank=True)
    pdf_material = models.FileField(
        upload_to='tutor/lesson_materials/',
        blank=True,
        validators=[FileExtensionValidator(['pdf'])],
    )
    created_at = models.DateTimeField(auto_now_add=True)


class Assignment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=180)
    description = models.TextField()
    due_date = models.DateTimeField()


class Submission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tutor_submissions')
    file = models.FileField(upload_to='tutor/submissions/')
    grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('assignment', 'student')
