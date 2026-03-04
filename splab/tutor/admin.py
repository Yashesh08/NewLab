from django.contrib import admin

from .models import Assignment, Course, Enrollment, Lesson, Submission, Tutor

admin.site.register(Tutor)
admin.site.register(Course)
admin.site.register(Enrollment)
admin.site.register(Lesson)
admin.site.register(Assignment)
admin.site.register(Submission)
