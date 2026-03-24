from django.conf import settings
from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Course(TimeStampedModel):
    class Level(models.TextChoices):
        BEGINNER = 'beginner', 'Beginner'
        INTERMEDIATE = 'intermediate', 'Intermediate'
        ADVANCED = 'advanced', 'Advanced'

    title = models.CharField(max_length=180)
    slug = models.SlugField(max_length=220, unique=True)
    category = models.CharField(max_length=80)
    short_description = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    level = models.CharField(max_length=20, choices=Level.choices, default=Level.BEGINNER)
    duration_weeks = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses_taught',
    )
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title


class Enrollment(TimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        COMPLETED = 'completed', 'Completed'
        PAUSED = 'paused', 'Paused'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    progress_percent = models.PositiveSmallIntegerField(default=0)
    enrolled_on = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'course')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} - {self.course}'


class CourseSection(TimeStampedModel):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='sections')
    title = models.CharField(max_length=150)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['course', 'order', 'id']

    def __str__(self):
        return f'{self.course.title}: {self.title}'


class VideoLecture(TimeStampedModel):
    section = models.ForeignKey(CourseSection, on_delete=models.CASCADE, related_name='lectures')
    title = models.CharField(max_length=180)
    video_url = models.URLField()
    duration_minutes = models.PositiveIntegerField(default=1)
    order = models.PositiveIntegerField(default=1)
    is_preview = models.BooleanField(default=False)

    class Meta:
        ordering = ['section', 'order', 'id']

    def __str__(self):
        return self.title


class CourseNote(TimeStampedModel):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='notes')
    title = models.CharField(max_length=150)
    file_url = models.URLField(blank=True)
    content = models.TextField(blank=True)

    class Meta:
        ordering = ['course', 'title']

    def __str__(self):
        return self.title


class Assignment(TimeStampedModel):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=180)
    instructions = models.TextField()
    due_at = models.DateTimeField()
    max_score = models.PositiveIntegerField(default=100)

    class Meta:
        ordering = ['due_at']

    def __str__(self):
        return self.title


class AssignmentSubmission(TimeStampedModel):
    class Status(models.TextChoices):
        SUBMITTED = 'submitted', 'Submitted'
        REVIEWED = 'reviewed', 'Reviewed'
        LATE = 'late', 'Late'

    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='assignment_submissions')
    submission_url = models.URLField(blank=True)
    remarks = models.TextField(blank=True)
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SUBMITTED)

    class Meta:
        unique_together = ('assignment', 'user')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.assignment.title} - {self.user}'


class LiveMeet(TimeStampedModel):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='live_meets')
    topic = models.CharField(max_length=180)
    scheduled_at = models.DateTimeField()
    meeting_url = models.URLField()
    duration_minutes = models.PositiveIntegerField(default=60)

    class Meta:
        ordering = ['scheduled_at']

    def __str__(self):
        return f'{self.course.title}: {self.topic}'
