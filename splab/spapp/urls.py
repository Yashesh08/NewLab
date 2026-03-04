from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('courses/', views.courses, name='courses'),
    path('courses/<slug:slug>/', views.course_detail, name='course_detail'),
    path('my-courses/<slug:slug>/', views.my_course_detail, name='my_course_detail'),
    path('instructors/', views.instructors, name='instructors'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # Tutor panel routes
    path('tutor/dashboard/', views.tutor_dashboard, name='tutor_dashboard'),
    path('tutor/courses/', views.tutor_courses, name='tutor_courses'),
    path('tutor/course/create/', views.tutor_course_create, name='tutor_course_create'),
    path('tutor/course/edit/<int:course_id>/', views.tutor_course_edit, name='tutor_course_edit'),
    path('tutor/course/delete/<int:course_id>/', views.tutor_course_delete, name='tutor_course_delete'),
    path('tutor/students/', views.tutor_students, name='tutor_students'),
    path('tutor/assignments/', views.tutor_assignments, name='tutor_assignments'),
    path('tutor/assignments/submission/<int:submission_id>/grade/', views.tutor_grade_submission, name='tutor_grade_submission'),
    path('tutor/content/', views.tutor_content, name='tutor_content'),
    path('tutor/analytics/', views.tutor_analytics, name='tutor_analytics'),
    path('tutor/profile/', views.tutor_profile, name='tutor_profile'),

    # API endpoints
    path('api/tutor/dashboard', views.api_tutor_dashboard, name='api_tutor_dashboard'),
    path('api/tutor/courses', views.api_tutor_courses, name='api_tutor_courses'),
    path('api/tutor/course', views.api_tutor_course_create, name='api_tutor_course_create'),
    path('api/tutor/course/<int:course_id>', views.api_tutor_course_detail, name='api_tutor_course_detail'),
    path('api/tutor/students', views.api_tutor_students, name='api_tutor_students'),
    path('api/tutor/analytics', views.api_tutor_analytics, name='api_tutor_analytics'),

    path('assignments/<int:assignment_id>/submit/', views.submit_assignment, name='submit_assignment'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
]
