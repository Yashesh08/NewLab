from django.urls import path

from . import views

urlpatterns = [
    # Tutor URLs are served from tutor.urls to avoid duplication/conflicts.
    path('', views.home, name='home'),
    path('courses/', views.courses, name='courses'),
    path('courses/<slug:slug>/', views.course_detail, name='course_detail'),
    path('my-courses/<slug:slug>/', views.my_course_detail, name='my_course_detail'),
    path('instructors/', views.instructors, name='instructors'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
]
