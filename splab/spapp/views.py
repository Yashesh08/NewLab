from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Avg, Count, Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .forms import AssignmentForm, CourseForm, LessonForm, SubmissionGradeForm, TutorProfileForm
from .models import Assignment, Course, Enrollment, Lesson, Submission, Tutor, UserProfile


COURSE_CATALOG = {
    'full-stack-javascript-bootcamp': {
        'title': 'Full-Stack JavaScript Bootcamp',
        'category': 'Development',
        'price': '49.00',
        'description': 'Learn HTML, CSS, JavaScript, Node.js, and MongoDB by building complete end-to-end applications.'
    },
    'react-for-intermediate-developers': {
        'title': 'React for Intermediate Developers',
        'category': 'Development',
        'price': '59.00',
        'description': 'Master hooks, routing, performance optimization, and reusable component architecture in real projects.'
    },
}


def get_user_role(user):
    if user.is_staff or user.is_superuser:
        return UserProfile.Role.ADMIN
    if not user.is_authenticated:
        return None
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile.role


def ensure_tutor(user):
    tutor, _ = Tutor.objects.get_or_create(user=user)
    return tutor


def role_required(allowed_roles):
    def decorator(view_func):
        @login_required
        def wrapped(request, *args, **kwargs):
            role = get_user_role(request.user)
            if role not in allowed_roles:
                messages.error(request, 'You are not authorized to access this panel.')
                return redirect('dashboard')
            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator


def home(request):
    return render(request, 'home.html', {'active_page': 'home'})


def courses(request):
    courses_qs = Course.objects.select_related('tutor__user').all()
    if not courses_qs.exists():
        return render(request, 'courses.html', {'active_page': 'courses', 'courses': [
            {'slug': slug, 'title': data['title'], 'category': data['category'], 'price': data['price'], 'description': data['description'], 'level': 'Beginner', 'duration': 'Self-paced'}
            for slug, data in COURSE_CATALOG.items()
        ], 'purchased_courses': []})

    purchased_courses = []
    if request.user.is_authenticated:
        purchased_courses = Course.objects.filter(enrollments__student=request.user).distinct()
    return render(request, 'courses.html', {'active_page': 'courses', 'courses': courses_qs, 'purchased_courses': purchased_courses})


def course_detail(request, slug):
    course = get_object_or_404(Course.objects.select_related('tutor__user'), slug=slug)
    return render(request, 'course_detail.html', {'active_page': 'courses', 'course': course})



def my_course_detail(request, slug):
    course = get_object_or_404(Course, slug=slug)
    lessons = course.lessons.all()
    assignments = course.assignments.all()
    return render(request, 'my_course_detail.html', {'active_page': 'courses', 'course': course, 'lessons': lessons, 'assignments': assignments})

def instructors(request):
    tutors = Tutor.objects.select_related('user').all()
    return render(request, 'instructors.html', {'active_page': 'instructors', 'tutors': tutors})


@login_required
def dashboard(request):
    role = get_user_role(request.user)
    if role == UserProfile.Role.TUTOR:
        return redirect('tutor_dashboard')
    return render(request, 'dashboard.html', {'active_page': 'dashboard', 'role': role})


@role_required({UserProfile.Role.TUTOR})
def tutor_dashboard(request):
    tutor = ensure_tutor(request.user)
    courses = Course.objects.filter(tutor=tutor)
    enrollments = Enrollment.objects.filter(course__tutor=tutor)
    submissions = Submission.objects.filter(assignment__course__tutor=tutor)

    dashboard_stats = {
        'total_courses': courses.count(),
        'total_students': enrollments.values('student').distinct().count(),
        'active_enrollments': enrollments.filter(status=Enrollment.Status.ACTIVE).count(),
        'pending_assignments': Assignment.objects.filter(course__tutor=tutor, due_date__gte=timezone.now()).count(),
        'course_rating_avg': round(courses.aggregate(avg=Avg('tutor__rating'))['avg'] or 0, 2),
    }

    recent_enrollments = enrollments.select_related('student', 'course')[:5]
    latest_submissions = submissions.select_related('student', 'assignment')[:5]
    student_activity = enrollments.select_related('student', 'course').order_by('-last_activity')[:6]

    return render(request, 'tutor_dashboard.html', {
        'active_page': 'tutor_dashboard',
        'dashboard_stats': dashboard_stats,
        'recent_enrollments': recent_enrollments,
        'latest_submissions': latest_submissions,
        'student_activity': student_activity,
    })


@role_required({UserProfile.Role.TUTOR})
def tutor_courses(request):
    tutor = ensure_tutor(request.user)
    courses = Course.objects.filter(tutor=tutor)
    return render(request, 'tutor_courses.html', {'active_page': 'tutor_courses', 'courses': courses})


@role_required({UserProfile.Role.TUTOR})
def tutor_course_create(request):
    tutor = ensure_tutor(request.user)
    form = CourseForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        course = form.save(commit=False)
        course.tutor = tutor
        course.save()
        messages.success(request, 'Course created successfully.')
        return redirect('tutor_courses')
    return render(request, 'tutor_course_create.html', {'active_page': 'tutor_courses', 'form': form})


@role_required({UserProfile.Role.TUTOR})
def tutor_course_edit(request, course_id):
    tutor = ensure_tutor(request.user)
    course = get_object_or_404(Course, id=course_id, tutor=tutor)
    form = CourseForm(request.POST or None, request.FILES or None, instance=course)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Course updated successfully.')
        return redirect('tutor_courses')
    return render(request, 'tutor_course_create.html', {'active_page': 'tutor_courses', 'form': form, 'is_edit': True})


@role_required({UserProfile.Role.TUTOR})
@require_http_methods(['POST'])
def tutor_course_delete(request, course_id):
    tutor = ensure_tutor(request.user)
    course = get_object_or_404(Course, id=course_id, tutor=tutor)
    course.delete()
    messages.success(request, 'Course deleted successfully.')
    return redirect('tutor_courses')


@role_required({UserProfile.Role.TUTOR})
def tutor_students(request):
    tutor = ensure_tutor(request.user)
    students = Enrollment.objects.filter(course__tutor=tutor).select_related('student', 'course')
    return render(request, 'tutor_students.html', {'active_page': 'tutor_students', 'students': students})


@role_required({UserProfile.Role.TUTOR})
def tutor_assignments(request):
    tutor = ensure_tutor(request.user)
    form = AssignmentForm(request.POST or None)
    form.fields['course'].queryset = Course.objects.filter(tutor=tutor)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Assignment created successfully.')
        return redirect('tutor_assignments')

    assignments = Assignment.objects.filter(course__tutor=tutor).prefetch_related('submissions')
    return render(request, 'tutor_assignments.html', {'active_page': 'tutor_assignments', 'form': form, 'assignments': assignments})


@role_required({UserProfile.Role.TUTOR})
@require_http_methods(['POST'])
def tutor_grade_submission(request, submission_id):
    tutor = ensure_tutor(request.user)
    submission = get_object_or_404(Submission, id=submission_id, assignment__course__tutor=tutor)
    form = SubmissionGradeForm(request.POST, instance=submission)
    if form.is_valid():
        form.save()
        messages.success(request, 'Submission graded successfully.')
    else:
        messages.error(request, 'Invalid grade value.')
    return redirect('tutor_assignments')


@role_required({UserProfile.Role.TUTOR})
def tutor_content(request):
    tutor = ensure_tutor(request.user)
    form = LessonForm(request.POST or None, request.FILES or None)
    form.fields['course'].queryset = Course.objects.filter(tutor=tutor)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Lesson added successfully.')
        return redirect('tutor_content')

    lessons = Lesson.objects.filter(course__tutor=tutor).select_related('course')
    return render(request, 'tutor_content.html', {'active_page': 'tutor_content', 'form': form, 'lessons': lessons})


@role_required({UserProfile.Role.TUTOR})
def tutor_analytics(request):
    tutor = ensure_tutor(request.user)
    enrollments = Enrollment.objects.filter(course__tutor=tutor)
    assignments = Assignment.objects.filter(course__tutor=tutor)
    submissions = Submission.objects.filter(assignment__course__tutor=tutor)

    completion_rate = enrollments.filter(status=Enrollment.Status.COMPLETED).count()
    completion_rate = round((completion_rate / enrollments.count()) * 100, 2) if enrollments.exists() else 0

    submission_rate = round((submissions.count() / assignments.count()) * 100, 2) if assignments.exists() else 0

    course_labels = list(Course.objects.filter(tutor=tutor).values_list('title', flat=True))
    enrollments_per_course = [
        Enrollment.objects.filter(course__title=course_title, course__tutor=tutor).count()
        for course_title in course_labels
    ]

    monthly_new_students = [
        Enrollment.objects.filter(course__tutor=tutor, enrolled_at__month=month).values('student').distinct().count()
        for month in range(1, 13)
    ]

    return render(request, 'tutor_analytics.html', {
        'active_page': 'tutor_analytics',
        'completion_rate': completion_rate,
        'submission_rate': submission_rate,
        'course_labels': course_labels,
        'enrollments_per_course': enrollments_per_course,
        'monthly_new_students': monthly_new_students,
    })


@role_required({UserProfile.Role.TUTOR})
def tutor_profile(request):
    tutor = ensure_tutor(request.user)
    form = TutorProfileForm(request.POST or None, request.FILES or None, instance=tutor)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Tutor profile updated successfully.')
        return redirect('tutor_profile')
    return render(request, 'tutor_profile.html', {'active_page': 'tutor_profile', 'form': form})


@role_required({UserProfile.Role.STUDENT})
@require_http_methods(['POST'])
def submit_assignment(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    file_value = request.FILES.get('file_url')
    if not file_value:
        messages.error(request, 'Please upload a valid assignment file.')
        return redirect('dashboard')
    Submission.objects.update_or_create(
        assignment=assignment,
        student=request.user,
        defaults={'file_url': file_value},
    )
    messages.success(request, 'Assignment submitted successfully.')
    return redirect('dashboard')


# API ENDPOINTS
@role_required({UserProfile.Role.TUTOR})
def api_tutor_dashboard(request):
    tutor = ensure_tutor(request.user)
    data = {
        'total_courses': Course.objects.filter(tutor=tutor).count(),
        'total_students': Enrollment.objects.filter(course__tutor=tutor).values('student').distinct().count(),
        'active_enrollments': Enrollment.objects.filter(course__tutor=tutor, status=Enrollment.Status.ACTIVE).count(),
        'pending_assignments': Assignment.objects.filter(course__tutor=tutor, due_date__gte=timezone.now()).count(),
    }
    return JsonResponse(data)


@role_required({UserProfile.Role.TUTOR})
def api_tutor_courses(request):
    tutor = ensure_tutor(request.user)
    courses = list(Course.objects.filter(tutor=tutor).values('id', 'title', 'category', 'price', 'created_at'))
    return JsonResponse({'courses': courses})


@role_required({UserProfile.Role.TUTOR})
@require_http_methods(['POST'])
def api_tutor_course_create(request):
    form = CourseForm(request.POST, request.FILES)
    if form.is_valid():
        course = form.save(commit=False)
        course.tutor = ensure_tutor(request.user)
        course.save()
        return JsonResponse({'id': course.id, 'message': 'Course created'}, status=201)
    return JsonResponse({'errors': form.errors}, status=400)


@role_required({UserProfile.Role.TUTOR})
@require_http_methods(['PUT', 'DELETE'])
def api_tutor_course_detail(request, course_id):
    tutor = ensure_tutor(request.user)
    course = get_object_or_404(Course, id=course_id, tutor=tutor)
    if request.method == 'DELETE':
        course.delete()
        return JsonResponse({'message': 'Course deleted'})

    data = request.POST.copy()
    if not data:
        return JsonResponse({'error': 'PUT body parsing for form-data is required.'}, status=400)
    form = CourseForm(data, request.FILES, instance=course)
    if form.is_valid():
        form.save()
        return JsonResponse({'message': 'Course updated'})
    return JsonResponse({'errors': form.errors}, status=400)


@role_required({UserProfile.Role.TUTOR})
def api_tutor_students(request):
    tutor = ensure_tutor(request.user)
    students = list(
        Enrollment.objects.filter(course__tutor=tutor)
        .values('student__first_name', 'student__last_name', 'student__email', 'course__title', 'progress', 'last_activity')
    )
    return JsonResponse({'students': students})


@role_required({UserProfile.Role.TUTOR})
def api_tutor_analytics(request):
    tutor = ensure_tutor(request.user)
    enrollments = Enrollment.objects.filter(course__tutor=tutor)
    data = {
        'course_enrollments': list(enrollments.values('course__title').annotate(total=Count('id'))),
        'completion_rate': enrollments.filter(status=Enrollment.Status.COMPLETED).count(),
        'submission_rate': Submission.objects.filter(assignment__course__tutor=tutor).count(),
    }
    return JsonResponse(data)


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')

        user = authenticate(request, username=email, password=password)
        if user is None:
            messages.error(request, 'Invalid credentials. Please try again.')
            return render(request, 'login.html', {'active_page': 'login', 'email': email})

        login(request, user)
        role = get_user_role(user)
        request.session['user_role'] = role
        if role == UserProfile.Role.TUTOR:
            return redirect('tutor_dashboard')
        return redirect('dashboard')

    return render(request, 'login.html', {'active_page': 'login'})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        role = request.POST.get('user_role', UserProfile.Role.STUDENT)

        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'register.html', {'active_page': 'register'})

        if User.objects.filter(username=email).exists():
            messages.error(request, 'An account with this email already exists.')
            return render(request, 'register.html', {'active_page': 'register'})

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        UserProfile.objects.create(user=user, role=role)
        if role == UserProfile.Role.TUTOR:
            Tutor.objects.create(user=user)

        login(request, user)
        request.session['user_role'] = role
        return redirect('tutor_dashboard' if role == UserProfile.Role.TUTOR else 'dashboard')

    return render(request, 'register.html', {'active_page': 'register'})


@login_required
def logout_view(request):
    logout(request)
    return redirect('home')
