from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group, User
from django.core.mail import send_mail
from django.db.models import Avg, Count, Max
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.text import slugify
from .models import (
    Assignment,
    AssignmentSubmission,
    Course,
    CourseNote,
    CourseSection,
    Enrollment,
    Instructor,
    PlatformSettings,
    VideoLecture,
)


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
    """
    Send notification email to user.
    Returns True if successful, False otherwise.
    Automatically logs the backend and content when DEBUG.
    """
    backend = settings.EMAIL_BACKEND
    if settings.DEBUG:
        # show what will be sent
        print("[email debug] backend=", backend)
        print("[email debug] to=", to_email)
        print("[email debug] subject=", subject)
        print("[email debug] message=\n", message)
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'purohityashesh@gmail.com'),
            recipient_list=[to_email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        # Log the error for debugging
        print(f"Email sending failed: {str(e)}")
        return False



def _is_instructor(user):
    if not user.is_authenticated:
        return False
    return user.groups.filter(name='Instructor').exists()

def _is_admin(user):
    if not user.is_authenticated:
        return False
    return user.is_staff or user.is_superuser


def _get_user_role(user):
    if not user.is_authenticated:
        return 'guest'
    if _is_admin(user):
        return 'admin'
    if _is_instructor(user):
        return 'instructor'
    return 'user'




def admin_required(view_func):
    @login_required(login_url='login')
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not _is_admin(request.user):
            messages.error(request, 'Unauthorized: only admins can access admin dashboard pages.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)

    return _wrapped_view

def _generate_unique_slug(title):
    base_slug = slugify(title) or 'course'
    slug = base_slug
    counter = 1
    while Course.objects.filter(slug=slug).exists():
        counter += 1
        slug = f'{base_slug}-{counter}'
    return slug


def _get_instructor_courses(user):
    return (
        Course.objects
        .filter(instructors__name__iexact=user.get_full_name())
        .distinct()
        .order_by('title')
    )

def get_course(slug):
    settings_obj = _get_platform_settings()
    queryset = Course.objects.filter(is_published=True)
    if not settings_obj.courses_visible:
        queryset = queryset.none()
    course = queryset.prefetch_related('instructors').get(slug=slug)
    return course


def _get_platform_settings():
    settings_obj, _ = PlatformSettings.objects.get_or_create(
        pk=1,
        defaults={
            'platform_name': 'LearnSphere',
            'courses_visible': True,
        },
    )
    return settings_obj


def home(request):
    settings_obj = _get_platform_settings()
    courses_queryset = Course.objects.filter(is_published=True)
    if not settings_obj.courses_visible:
        courses_queryset = courses_queryset.none()
    courses = list(courses_queryset.order_by('title'))
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
    settings_obj = _get_platform_settings()
    queryset = Course.objects.filter(is_published=True)
    if not settings_obj.courses_visible:
        queryset = queryset.none()
    queryset = queryset.order_by('title')
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
            'courses_visible': settings_obj.courses_visible,
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


@login_required(login_url='login')
def buy_course(request, slug):
    if request.method != 'POST':
        return redirect('course_detail', slug=slug)

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
            email_sent = _send_notification_email(
                to_email=request.user.email,
                subject=f'Course purchase confirmed: {course.title}',
                message=(
                    f'Hi {request.user.first_name or "Learner"},\n\n'
                    f'Your purchase for "{course.title}" is confirmed.\n'
                    'You can now access all course content from your dashboard.\n\n'
                    'Thanks for learning with LearnSphere!'
                ),
            )
            if email_sent:
                messages.success(request, 'Purchase successful! A confirmation email has been sent.')
            else:
                messages.warning(request, 'Purchase successful, but email confirmation could not be sent.')
        except Exception as e:
            print(f"Error during course purchase email: {str(e)}")
            messages.warning(request, 'Purchase successful, but we could not send the confirmation email right now.')
    else:
        if enrollment.status == Enrollment.Status.PAUSED:
            enrollment.status = Enrollment.Status.ACTIVE
            enrollment.save(update_fields=['status', 'updated_at'])
        messages.info(request, 'You already own this course. Opening your course workspace.')

    return redirect('my_course_detail', slug=slug)


@login_required(login_url='login')
def my_course_detail(request, slug):

    try:
        enrollment = (
            Enrollment.objects
            .select_related('course')
            .prefetch_related('course__sections__lectures', 'course__notes', 'course__live_meets', 'course__assignments')
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

    assignments = list(course.assignments.order_by('due_at'))
    attempts = {
        attempt.assignment_id: attempt
        for attempt in AssignmentSubmission.objects.filter(user=request.user, assignment__course=course).select_related('assignment')
    }
    assignment_rows = [
        {
            'assignment': assignment,
            'attempt': attempts.get(assignment.id),
        }
        for assignment in assignments
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
            'assignment_rows': assignment_rows,
        },
    )


def instructors(request):
    instructors_list = Instructor.objects.filter(is_active=True).values('name', 'title', 'bio')
    return render(request, 'instructors.html', {'active_page': 'instructors', 'instructors': instructors_list})


@login_required(login_url='login')
def dashboard(request):

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


@login_required(login_url='login')
def profile_view(request):
    user_role = _get_user_role(request.user)
    instructor_profile = None
    if user_role == 'instructor':
        instructor_profile = Instructor.objects.filter(name__iexact=request.user.get_full_name()).first()

    context = {
        'active_page': 'profile',
        'user_role': user_role,
        'user_obj': request.user,
        'instructor_profile': instructor_profile,
    }
    return render(request, 'profile.html', context)


@login_required(login_url='login')
def edit_profile(request):
    user_role = _get_user_role(request.user)
    instructor_profile = None
    if user_role == 'instructor':
        instructor_profile = Instructor.objects.filter(name__iexact=request.user.get_full_name()).first()

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip().lower()

        if not all([first_name, last_name, email]):
            messages.error(request, 'First name, last name, and email are required.')
            return redirect('edit_profile')

        email_in_use = User.objects.filter(email=email).exclude(id=request.user.id).exists()
        if email_in_use:
            messages.error(request, 'This email is already in use by another account.')
            return redirect('edit_profile')

        previous_full_name = request.user.get_full_name()

        request.user.first_name = first_name
        request.user.last_name = last_name
        request.user.email = email
        request.user.username = email
        request.user.save(update_fields=['first_name', 'last_name', 'email', 'username'])

        if user_role == 'instructor':
            title = request.POST.get('title', '').strip() or 'Instructor'
            bio = request.POST.get('bio', '').strip() or 'Auto-created instructor profile.'
            current_full_name = request.user.get_full_name()

            if instructor_profile is None and current_full_name:
                instructor_profile, _ = Instructor.objects.get_or_create(
                    name=current_full_name,
                    defaults={'title': title, 'bio': bio},
                )
            elif instructor_profile is not None:
                instructor_profile.name = current_full_name or instructor_profile.name
                instructor_profile.title = title
                instructor_profile.bio = bio
                instructor_profile.save(update_fields=['name', 'title', 'bio', 'updated_at'])

            if previous_full_name and current_full_name and previous_full_name != current_full_name:
                Instructor.objects.filter(name__iexact=previous_full_name).exclude(id=getattr(instructor_profile, 'id', None)).update(
                    name=current_full_name
                )

        messages.success(request, 'Profile updated successfully.')
        return redirect('profile')

    context = {
        'active_page': 'profile',
        'user_role': user_role,
        'user_obj': request.user,
        'instructor_profile': instructor_profile,
    }
    return render(request, 'profile_edit.html', context)


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
        user_type = request.POST.get('user_type', 'user').strip().lower()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        register_context = {
            'active_page': 'register',
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'user_type': user_type,
        }

        allowed_user_types = {'user', 'instructor', 'admin'}
        if user_type not in allowed_user_types:
            messages.error(request, 'Please choose a valid account type.')
            return render(request, 'register.html', register_context)

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
            is_staff=user_type == 'admin',
        )

        if user_type == 'instructor':
            instructors_group, _ = Group.objects.get_or_create(name='Instructor')
            user.groups.add(instructors_group)
            full_name = f'{first_name} {last_name}'.strip()
            if full_name:
                Instructor.objects.get_or_create(
                    name=full_name,
                    defaults={'title': 'Instructor', 'bio': 'Auto-created instructor profile.'},
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



@admin_required
def admin_panel(request):

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'create_course':
            title = request.POST.get('title', '').strip()
            category = request.POST.get('category', '').strip()
            short_description = request.POST.get('short_description', '').strip()
            description = request.POST.get('description', '').strip()
            level = request.POST.get('level', Course.Level.BEGINNER)
            duration_weeks = request.POST.get('duration_weeks', '1').strip()
            price = request.POST.get('price', '0').strip()
            instructor_ids = request.POST.getlist('instructor_ids')

            if not all([title, category, short_description]):
                messages.error(request, 'Title, category, and short description are required.')
                return redirect('admin_panel')

            try:
                duration_weeks_value = max(1, int(duration_weeks))
                price_value = max(0, float(price))
            except ValueError:
                messages.error(request, 'Duration and price must be valid numbers.')
                return redirect('admin_panel')

            course = Course.objects.create(
                title=title,
                slug=_generate_unique_slug(title),
                category=category,
                short_description=short_description,
                description=description,
                level=level if level in Course.Level.values else Course.Level.BEGINNER,
                duration_weeks=duration_weeks_value,
                price=price_value,
                is_published=True,
            )
            if instructor_ids:
                course.instructors.set(Instructor.objects.filter(id__in=instructor_ids, is_active=True))

            messages.success(request, f'Course "{course.title}" created and instructor mapping saved.')
            return redirect('admin_panel')

    total_users = User.objects.count()
    total_courses = Course.objects.count()
    total_enrollments = Enrollment.objects.count()
    active_enrollments = Enrollment.objects.filter(status=Enrollment.Status.ACTIVE).count()

    recent_users = User.objects.order_by('-date_joined')[:5]
    all_users = User.objects.order_by('-date_joined')
    recent_courses = Course.objects.order_by('-created_at')[:5]
    enrollment_rows = (
        Enrollment.objects
        .select_related('user', 'course')
        .order_by('-created_at')
    )

    context = {
        'active_page': 'admin_panel',
        'total_users': total_users,
        'total_courses': total_courses,
        'total_enrollments': total_enrollments,
        'active_enrollments': active_enrollments,
        'recent_users': recent_users,
        'all_users': all_users,
        'recent_courses': recent_courses,
        'enrollment_rows': enrollment_rows,
        'instructors': Instructor.objects.filter(is_active=True).order_by('name'),
        'course_levels': Course.Level.choices,
    }
    return render(request, 'admin_panel.html', context)


@admin_required
def admin_settings(request):
    settings_obj = _get_platform_settings()

    if request.method == 'POST':
        platform_name = request.POST.get('platform_name', '').strip()
        settings_obj.platform_name = platform_name or 'LearnSphere'
        settings_obj.courses_visible = request.POST.get('courses_visible') == 'on'
        settings_obj.save(update_fields=['platform_name', 'courses_visible', 'updated_at'])
        messages.success(request, 'System settings updated successfully.')
        return redirect('admin_settings')

    return render(
        request,
        'admin_settings.html',
        {
            'active_page': 'admin_panel',
            'settings_obj': settings_obj,
        },
    )


@admin_required
def delete_user(request, user_id):
    """Delete a user from the system."""
    
    user_to_delete = User.objects.filter(id=user_id).first()
    
    if not user_to_delete:
        messages.error(request, 'User not found.')
        return redirect('admin_panel')
    
    # Prevent admins from deleting themselves
    if user_to_delete.id == request.user.id:
        messages.error(request, 'You cannot delete your own admin account.')
        return redirect('admin_panel')
    
    user_name = user_to_delete.get_full_name() or user_to_delete.username
    user_email = user_to_delete.email
    
    # Delete associated enrollments, submissions, and notes first
    enrollments = Enrollment.objects.filter(user=user_to_delete)
    for enrollment in enrollments:
        AssignmentSubmission.objects.filter(user=user_to_delete, assignment__course=enrollment.course).delete()
    enrollments.delete()
    
    # Delete the user
    user_to_delete.delete()
    
    messages.success(request, f'User "{user_name}" ({user_email}) has been successfully deleted.')
    return redirect('admin_panel')
@user_passes_test(_is_instructor, login_url='home', redirect_field_name=None)
def instructor_panel(request):

    courses_taught = _get_instructor_courses(request.user)

    course_rows = [
        {
            'id': course.id,
            'title': course.title,
            'category': course.category,
            'level': course.get_level_display(),
            'enrollment_count': course.enrollments.count(),
            'materials_count': course.notes.count() + course.sections.count(),
            'tests_count': course.assignments.count(),
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


@login_required(login_url='login')
@user_passes_test(_is_instructor, login_url='home', redirect_field_name=None)
def manage_instructor_course(request, course_id):
    course = _get_instructor_courses(request.user).filter(id=course_id).first()
    if course is None:
        messages.error(request, 'Course not found in your instructor assignment list.')
        return redirect('instructor_panel')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add_section':
            section_title = request.POST.get('section_title', '').strip()
            if section_title:
                next_order = (course.sections.aggregate(max_order=Max('order')).get('max_order') or 0) + 1
                CourseSection.objects.create(course=course, title=section_title, order=next_order)
                messages.success(request, 'Section added successfully.')
            else:
                messages.error(request, 'Section title is required.')

        elif action == 'add_video':
            section_id = request.POST.get('section_id')
            title = request.POST.get('video_title', '').strip()
            video_url = request.POST.get('video_url', '').strip()
            duration = request.POST.get('duration_minutes', '1').strip()

            section = course.sections.filter(id=section_id).first()
            if not section or not title or not video_url:
                messages.error(request, 'Section, title, and video URL are required for lecture.')
            else:
                try:
                    duration_value = max(1, int(duration))
                except ValueError:
                    duration_value = 1
                next_order = section.lectures.count() + 1
                VideoLecture.objects.create(
                    section=section,
                    title=title,
                    video_url=video_url,
                    duration_minutes=duration_value,
                    order=next_order,
                )
                messages.success(request, 'Video lecture added.')

        elif action == 'add_note':
            note_title = request.POST.get('note_title', '').strip()
            note_content = request.POST.get('note_content', '').strip()
            note_file_url = request.POST.get('note_file_url', '').strip()
            if not note_title:
                messages.error(request, 'Material title is required.')
            else:
                CourseNote.objects.create(course=course, title=note_title, content=note_content, file_url=note_file_url)
                messages.success(request, 'Material added successfully.')

        elif action == 'add_test':
            test_title = request.POST.get('test_title', '').strip()
            instructions = request.POST.get('instructions', '').strip()
            due_at_raw = request.POST.get('due_at', '').strip()
            max_score_raw = request.POST.get('max_score', '100').strip()

            if not all([test_title, instructions, due_at_raw]):
                messages.error(request, 'Test title, instructions, and due date are required.')
            else:
                try:
                    due_at = timezone.datetime.fromisoformat(due_at_raw)
                    due_at = timezone.make_aware(due_at) if timezone.is_naive(due_at) else due_at
                except ValueError:
                    messages.error(request, 'Invalid due date format.')
                    return redirect('manage_instructor_course', course_id=course.id)

                try:
                    max_score = max(1, int(max_score_raw))
                except ValueError:
                    max_score = 100
                Assignment.objects.create(
                    course=course,
                    title=test_title,
                    instructions=instructions,
                    due_at=due_at,
                    max_score=max_score,
                )
                messages.success(request, 'Test added successfully.')

        return redirect('manage_instructor_course', course_id=course.id)

    context = {
        'active_page': 'instructor_panel',
        'course': course,
        'sections': course.sections.order_by('order', 'id'),
        'notes': course.notes.order_by('title'),
        'assignments': course.assignments.order_by('due_at'),
    }
    return render(request, 'instructor_course_manage.html', context)


@login_required(login_url='login')
def attempt_test(request, slug, assignment_id):
    if request.method != 'POST':
        return redirect('my_course_detail', slug=slug)

    enrollment = Enrollment.objects.filter(user=request.user, course__slug=slug).select_related('course').first()
    if not enrollment:
        raise Http404('Course not purchased')

    assignment = Assignment.objects.filter(id=assignment_id, course=enrollment.course).first()
    if not assignment:
        raise Http404('Test not found')

    answer_text = request.POST.get('answer_text', '').strip()
    submission_url = request.POST.get('submission_url', '').strip()

    if not answer_text and not submission_url:
        messages.error(request, 'Please provide an answer text or submission URL.')
        return redirect('my_course_detail', slug=slug)

    submission, _ = AssignmentSubmission.objects.update_or_create(
        assignment=assignment,
        user=request.user,
        defaults={
            'remarks': answer_text,
            'submission_url': submission_url,
            'status': AssignmentSubmission.Status.SUBMITTED,
        },
    )
    messages.success(request, f'Your attempt for "{submission.assignment.title}" has been submitted.')
    return redirect('my_course_detail', slug=slug)

@login_required(login_url='login')
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')
