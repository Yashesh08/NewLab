from django.contrib import admin

from .models import (
    Assignment,
    AssignmentSubmission,
    Course,
    CourseNote,
    CourseSection,
    Enrollment,
    LiveMeet,
    VideoLecture,
)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'instructor', 'category', 'level', 'price', 'is_published')
    search_fields = ('title', 'category', 'instructor__username', 'instructor__first_name', 'instructor__last_name')
    list_filter = ('category', 'level', 'is_published')
    prepopulated_fields = {'slug': ('title',)}


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'status', 'progress_percent', 'enrolled_on')
    list_filter = ('status', 'enrolled_on')
    search_fields = ('user__username', 'course__title')


admin.site.register(CourseSection)
admin.site.register(VideoLecture)
admin.site.register(CourseNote)
admin.site.register(Assignment)
admin.site.register(AssignmentSubmission)
admin.site.register(LiveMeet)
