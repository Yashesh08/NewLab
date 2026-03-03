from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db.models import Avg, Count
from django.http import Http404
from django.shortcuts import redirect, render

from .models import Course, Enrollment, Instructor


HOME_FEATURES = [
    {
        'title': 'Structured Curriculum',
        'description': 'Weekly plans with concept videos, notes, coding labs, and auto-tracked progress to avoid overwhelm.',
    },
    {
        'title': 'Assignments + Feedback',
        'description': 'Work on practical tasks and get rubric-based feedback from mentors to improve with every submission.',
    },
    {
        'title': 'Live Doubt Sessions',
        'description': 'Join regular live classes, group Q&A, and problem-solving meets to accelerate your growth.',
    },
    {
        'title': 'Community Learning',
        'description': 'Learn with peers in cohorts, take part in hackathons, and collaborate through study circles.',
    },
    {
        'title': 'Career Services',
        'description': 'Resume clinics, mock interviews, portfolio reviews, and referral networks for job opportunities.',
    },
    {
        'title': 'Mobile Friendly',
        'description': 'Continue learning on mobile with downloadable notes and saved lessons for your commute.',
    },
]


def _course_to_dict(course):
    return {
        'slug': course.slug,
        'title': course.title,
        'category': course.category,
        'level': course.get_level_display(),
        'duration': f'{course.duration_weeks} weeks',
        'price': f'${course.price}',
        'description': course.description or course.short_description,
        'short_description': course.short_description,
    }


def _send_notification_email(to_email, subject, message):
    send_mail(
        subject=subject,
        message=message,
        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'purohityashesh@gmail.com'),
        recipient_list=[to_email],
        fail_silently=False,
    )


def _is_instructor(user):
    if not user.is_authenticated:
        return False
    return user.groups.filter(name='Instructor').exists()


def _get_user_role(user):
    if not user.is_authenticated:
        return 'guest'
    if user.is_superuser or user.is_staff:
        return 'admin'
    if _is_instructor(user):
        return 'instructor'
    return 'user'


def get_course(slug):
    course = Course.objects.filter(is_published=True).prefetch_related('instructors').get(slug=slug)
    return course


def home(request):
    courses = list(Course.objects.filter(is_published=True).order_by('title'))
    featured_courses = courses[:3]

    badge_class_by_level = {
        'Beginner': 'success',
        'Intermediate': 'warning',
        'Advanced': 'danger',
    }
    featured_paths = []
    for index, course in enumerate(featured_courses, start=1):
        item = _course_to_dict(course)
        item['badge_text'] = f"{item['level']} Track"
        item['badge_class'] = badge_class_by_level.get(item['level'], 'warning')
        item['projects'] = 4 + index * 2
        featured_paths.append(item)

    stats = Course.objects.filter(is_published=True).aggregate(
        average_price=Avg('price'),
        category_count=Count('category', distinct=True),
        course_count=Count('id'),
    )

    active_enrollments = Enrollment.objects.filter(status=Enrollment.Status.ACTIVE).count()
    latest_course_title = featured_paths[0]['title'] if featured_paths else 'your first course'

    context = {
        'active_page': 'home',
        'hero_badge': 'New Cohort Starts 15th June',
        'hero_title': 'Build job-ready skills with a complete learning platform.',
        'hero_subtitle': (
            'LearnSphere combines structured learning paths, mentor support, hands-on assignments, '
            'and placement-focused prep so you can turn learning into real career growth.'
        ),
        'hero_metrics': [
            {'value': f'{active_enrollments}+', 'label': 'Active enrollments'},
            {'value': f"{stats.get('course_count') or 0}+", 'label': 'Industry-ready courses'},
            {'value': f"${round(float(stats.get('average_price') or 0), 1)}", 'label': 'Average course fee'},
            {'value': f"{stats.get('category_count') or 0}", 'label': 'Learning categories'},
        ],
        'learning_week': [
            f'✅ Complete "{latest_course_title}" lesson plan',
            '📝 Submit assignment before the weekly deadline',
            '🎥 Join the next live mentor session',
            f'🏆 Track progress across {active_enrollments} active enrollments',
        ],
        'partners': [name for name in Instructor.objects.filter(is_active=True).values_list('name', flat=True)[:5]],
        'featured_paths': featured_paths,
        'features': HOME_FEATURES,
    }

    return render(request, 'home.html', context)


def courses(request):
    queryset = Course.objects.filter(is_published=True).order_by('title')
    courses_list = [_course_to_dict(course) for course in queryset]

    purchased_courses = []
    if request.user.is_authenticated:
        enrollments = (
            Enrollment.objects
            .select_related('course')
            .filter(user=request.user)
            .exclude(status=Enrollment.Status.PAUSED)
        )
        purchased_courses = [_course_to_dict(item.course) for item in enrollments]

    return render(
        request,
        'courses.html',
        {
            'active_page': 'courses',
            'courses': courses_list,
            'purchased_courses': purchased_courses,
        },
    )


def course_detail(request, slug):
    try:
        course = get_course(slug)
    except Course.DoesNotExist as exc:
        raise Http404('Course not found') from exc

    is_enrolled = False
    if request.user.is_authenticated:
        is_enrolled = Enrollment.objects.filter(user=request.user, course=course).exists()

    return render(
        request,
        'course_detail.html',
        {
            'active_page': 'courses',
            'course': _course_to_dict(course),
            'slug': slug,
            'is_enrolled': is_enrolled,
        },
    )


def buy_course(request, slug):
    if request.method != 'POST':
        return redirect('course_detail', slug=slug)

    if not request.user.is_authenticated:
        messages.error(request, 'Please login before purchasing a course.')
        return redirect('login')

    try:
        course = get_course(slug)
    except Course.DoesNotExist as exc:
        raise Http404('Course not found') from exc

    enrollment, created = Enrollment.objects.get_or_create(
        user=request.user,
        course=course,
        defaults={'status': Enrollment.Status.ACTIVE, 'progress_percent': 0},
    )

    if created:
        try:
            _send_notification_email(
                to_email=request.user.email,
                subject=f'Course purchase confirmed: {course.title}',
                message=(
                    f'Hi {request.user.first_name or "Learner"},\n\n'
                    f'Your purchase for "{course.title}" is confirmed.\n'
                    'You can now access all course content from your dashboard.\n\n'
                    'Thanks for learning with LearnSphere!'
                ),
            )
            messages.success(request, 'Purchase successful! A confirmation email has been sent.')
        except Exception:
            messages.warning(request, 'Purchase successful, but we could not send the confirmation email right now.')
    else:
        if enrollment.status == Enrollment.Status.PAUSED:
            enrollment.status = Enrollment.Status.ACTIVE
            enrollment.save(update_fields=['status', 'updated_at'])
        messages.info(request, 'You already own this course. Opening your course workspace.')

    return redirect('my_course_detail', slug=slug)


def my_course_detail(request, slug):
    if not request.user.is_authenticated:
        messages.error(request, 'Please login to access purchased courses.')
        return redirect('login')

    try:
        enrollment = (
            Enrollment.objects
            .select_related('course')
            .prefetch_related('course__sections__lectures', 'course__notes', 'course__live_meets')
            .get(user=request.user, course__slug=slug)
        )
    except Enrollment.DoesNotExist as exc:
        raise Http404('Course not purchased') from exc

    course = enrollment.course
    module_outline = [section.title for section in course.sections.all()]
    notes = [note.title for note in course.notes.all()]
    video_lectures = [
        {'title': lecture.title, 'duration': f'{lecture.duration_minutes} min'}
        for section in course.sections.all()
        for lecture in section.lectures.all()
    ]
    upcoming_meets = [
        {'topic': meet.topic, 'date': meet.scheduled_at.strftime('%A, %I:%M %p')}
        for meet in course.live_meets.all()
    ]

    return render(
        request,
        'my_course_detail.html',
        {
            'active_page': 'courses',
            'course': _course_to_dict(course),
            'slug': slug,
            'module_outline': module_outline,
            'notes': notes,
            'video_lectures': video_lectures,
            'upcoming_meets': upcoming_meets,
        },
    )


def instructors(request):
    instructors_list = Instructor.objects.filter(is_active=True).values('name', 'title', 'bio')
    return render(request, 'instructors.html', {'active_page': 'instructors', 'instructors': instructors_list})


def dashboard(request):
    if not request.user.is_authenticated:
        messages.error(request, 'Please login to open your dashboard.')
        return redirect('login')

    enrollments = Enrollment.objects.filter(user=request.user).select_related('course').order_by('-created_at')
    courses_data = [
        {
            'course': item.course.title,
            'category': item.course.category,
            'progress': item.progress_percent,
            'status': item.status,
            'status_label': item.get_status_display(),
            'status_class': 'success' if item.status == Enrollment.Status.COMPLETED else 'warning',
        }
        for item in enrollments
    ]

    average_progress = round(
        sum(item['progress'] for item in courses_data) / len(courses_data),
        0,
    ) if courses_data else 0

    context = {
        'active_page': 'dashboard',
        'user_role': _get_user_role(request.user),
        'learning_goal': 8,
        'completed_hours': round((average_progress / 100) * 8, 1),
        'goal_progress': average_progress,
        'streak_days': min(30, len(courses_data) * 3),
        'courses_data': courses_data,
    }
    return render(request, 'dashboard.html', context)


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')

        if not email or not password:
            messages.error(request, 'Please enter both email and password.')
            return render(request, 'login.html', {'active_page': 'login', 'email': email})

        user = authenticate(request, username=email, password=password)
        if user is None:
            messages.error(request, 'Invalid credentials. Please try again.')
            return render(request, 'login.html', {'active_page': 'login', 'email': email})

        login(request, user)
        user_role = _get_user_role(user)
        messages.success(request, f'Welcome back, {user.first_name or "Learner"}!')
        if user_role == 'admin':
            return redirect('admin_panel')
        if user_role == 'instructor':
            return redirect('instructor_panel')
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

        register_context = {
            'active_page': 'register',
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
        }

        if not all([first_name, last_name, email, password, confirm_password]):
            messages.error(request, 'Please fill all required fields.')
            return render(request, 'register.html', register_context)

        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'register.html', register_context)

        if User.objects.filter(username=email).exists() or User.objects.filter(email=email).exists():
            messages.error(request, 'An account with this email already exists.')
            return render(request, 'register.html', register_context)

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        login(request, user)

        try:
            _send_notification_email(
                to_email=user.email,
                subject='Welcome to LearnSphere',
                message=(
                    f'Hi {user.first_name or "Learner"},\n\n'
                    'Your account has been created successfully on LearnSphere.\n'
                    'Start exploring courses and begin your learning journey today.\n\n'
                    'Thank you!'
                ),
            )
            messages.success(request, 'Account created successfully. A welcome email has been sent.')
        except Exception:
            messages.warning(request, 'Account created successfully, but we could not send the welcome email right now.')

        return redirect('dashboard')

    return render(request, 'register.html', {'active_page': 'register'})



def admin_panel(request):
    if not request.user.is_authenticated:
        messages.error(request, 'Please login as admin to access admin panel.')
        return redirect('login')

    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Only admin users can access the admin panel.')
        return redirect('home')

    total_users = User.objects.count()
    total_courses = Course.objects.count()
    total_enrollments = Enrollment.objects.count()
    active_enrollments = Enrollment.objects.filter(status=Enrollment.Status.ACTIVE).count()

    recent_users = User.objects.order_by('-date_joined')[:5]
    recent_courses = Course.objects.order_by('-created_at')[:5]

    context = {
        'active_page': 'admin_panel',
        'total_users': total_users,
        'total_courses': total_courses,
        'total_enrollments': total_enrollments,
        'active_enrollments': active_enrollments,
        'recent_users': recent_users,
        'recent_courses': recent_courses,
    }
    return render(request, 'admin_panel.html', context)


def instructor_panel(request):
    if not request.user.is_authenticated:
        messages.error(request, 'Please login as instructor to access instructor panel.')
        return redirect('login')

    if not _is_instructor(request.user):
        messages.error(request, 'Only instructor users can access the instructor panel.')
        return redirect('home')

    courses_taught = (
        Course.objects
        .filter(instructors__name__iexact=request.user.get_full_name())
        .distinct()
        .order_by('title')
    )
    if not courses_taught.exists():
        courses_taught = Course.objects.filter(is_published=True).order_by('title')[:5]

    course_rows = [
        {
            'title': course.title,
            'category': course.category,
            'level': course.get_level_display(),
            'enrollment_count': course.enrollments.count(),
        }
        for course in courses_taught
    ]

    context = {
        'active_page': 'instructor_panel',
        'course_rows': course_rows,
        'total_courses': len(course_rows),
        'total_enrollments': sum(item['enrollment_count'] for item in course_rows),
    }
    return render(request, 'instructor_panel.html', context)

def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, 'You have been logged out successfully.')
    return redirect('home')
