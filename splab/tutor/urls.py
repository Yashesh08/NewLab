from django.urls import path

from . import views

urlpatterns = [
    path('tutor/dashboard/', views.tutor_dashboard, name='tutor_dashboard'),
    path('tutor/courses/', views.tutor_courses, name='tutor_courses'),
    path('tutor/course/create/', views.create_course, name='create_course'),
    path('tutor/course/edit/<int:id>/', views.edit_course, name='edit_course'),
    path('tutor/course/delete/<int:id>/', views.delete_course, name='delete_course'),
    path('tutor/students/', views.tutor_students, name='tutor_students'),
    path('tutor/assignments/', views.tutor_assignments, name='tutor_assignments'),
    path('tutor/submission/<int:id>/grade/', views.grade_submission, name='grade_submission'),
    path('tutor/assignment/<int:id>/submit/', views.submit_assignment, name='submit_assignment'),
    path('tutor/analytics/', views.tutor_analytics, name='tutor_analytics'),
    path('tutor/profile/', views.tutor_profile, name='tutor_profile'),
]
