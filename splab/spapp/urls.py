from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('courses/', views.courses, name='courses'),
    path('courses/<slug:slug>/', views.course_detail, name='course_detail'),
    path('my-courses/<slug:slug>/', views.my_course_detail, name='my_course_detail'),
    path('instructors/', views.instructors, name='instructors'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('admin-panel/', views.admin_panel, name='admin_panel'),
    path('admin-panel/courses/', views.admin_course_list, name='admin_courses'),
    path('admin-panel/courses/new/', views.admin_course_create, name='admin_course_create'),
    path('admin-panel/courses/<int:course_id>/edit/', views.admin_course_edit, name='admin_course_edit'),
    path('admin-panel/courses/<int:course_id>/delete/', views.admin_course_delete, name='admin_course_delete'),
    path('admin-panel/instructors/', views.admin_instructor_list, name='admin_instructors'),
    path('admin-panel/instructors/new/', views.admin_instructor_create, name='admin_instructor_create'),
    path('admin-panel/instructors/<int:instructor_id>/edit/', views.admin_instructor_edit, name='admin_instructor_edit'),
    path('admin-panel/instructors/<int:instructor_id>/delete/', views.admin_instructor_delete, name='admin_instructor_delete'),
    path('admin-panel/students/', views.admin_student_list, name='admin_students'),
    path('admin-panel/students/<int:student_id>/', views.admin_student_detail, name='admin_student_detail'),
    path('admin-panel/students/<int:student_id>/deactivate/', views.admin_student_deactivate, name='admin_student_deactivate'),
    path('admin-panel/students/<int:student_id>/delete/', views.admin_student_delete, name='admin_student_delete'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
]
