from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from .forms import AdminCourseForm, AdminInstructorForm
from .models import Course, Enrollment, InstructorProfile

COURSE_CATALOG = {
    'full-stack-javascript-bootcamp': {
        'title': 'Full-Stack JavaScript Bootcamp',
        'category': 'Development',
        'level': 'Beginner',
        'duration': '10 weeks',
        'price': '$49',
        'description': 'Learn HTML, CSS, JavaScript, Node.js, and MongoDB by building complete end-to-end applications.',
    },
    'react-for-intermediate-developers': {
        'title': 'React for Intermediate Developers',
        'category': 'Development',
        'level': 'Intermediate',
        'duration': '6 weeks',
        'price': '$59',
        'description': 'Master hooks, routing, performance optimization, and reusable component architecture in real projects.',
    },
    'figma-ui-design-workshop': {
        'title': 'Figma UI Design Workshop',
        'category': 'Design',
        'level': 'Beginner',
        'duration': '4 weeks',
        'price': '$39',
        'description': 'Build polished user interfaces in Figma with practical workflows, components, and design handoff.',
    },
    'advanced-product-design-systems': {
        'title': 'Advanced Product Design Systems',
        'category': 'Design',
        'level': 'Advanced',
        'duration': '8 weeks',
        'price': '$69',
        'description': 'Create scalable design systems and governance practices for high-growth product teams.',
    },
    'growth-marketing-seo': {
        'title': 'Growth Marketing & SEO',
        'category': 'Marketing',
        'level': 'Intermediate',
        'duration': '5 weeks',
        'price': '$44',
        'description': 'Learn acquisition channels, SEO fundamentals, and conversion experiments to grow product adoption.',
    },
    'data-analytics-with-python': {
        'title': 'Data Analytics with Python',
        'category': 'Data',
        'level': 'Beginner',
        'duration': '7 weeks',
        'price': '$54',
        'description': 'Analyze and visualize datasets using Python, pandas, and practical business intelligence workflows.',
    },
}

PURCHASED_COURSE_SLUGS = [
    'full-stack-javascript-bootcamp',
    'figma-ui-design-workshop',
    'data-analytics-with-python',
]


def get_course(slug):
    course = COURSE_CATALOG.get(slug)
    if not course:
        raise Http404('Course not found')
    return course


def home(request):
    return render(request, 'home.html', {'active_page': 'home'})


def courses(request):
    courses_list = [{'slug': slug, **course} for slug, course in COURSE_CATALOG.items()]
    purchased_courses = [
        {'slug': slug, **COURSE_CATALOG[slug]}
        for slug in PURCHASED_COURSE_SLUGS
        if slug in COURSE_CATALOG
    ]
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
    course = get_course(slug)
    return render(
        request,
        'course_detail.html',
        {'active_page': 'courses', 'course': course, 'slug': slug},
    )


def my_course_detail(request, slug):
    course = get_course(slug)
    if slug not in PURCHASED_COURSE_SLUGS:
        raise Http404('Course not purchased')

    module_outline = [
        'Course orientation and setup',
        'Core concepts and fundamentals',
        'Hands-on implementation project',
        'Assessment, notes review, and final Q&A',
    ]
    notes = [
        'Key concepts summary and important formulas',
        'Interview questions and model answers',
        'Downloadable cheatsheet and glossary',
    ]
    video_lectures = [
        {'title': 'Welcome & roadmap', 'duration': '12 min'},
        {'title': 'Practical deep-dive lesson', 'duration': '34 min'},
        {'title': 'Project walkthrough', 'duration': '41 min'},
    ]
    upcoming_meets = [
        {'topic': 'Live doubt solving', 'date': 'Saturday, 6:00 PM'},
        {'topic': 'Project review clinic', 'date': 'Wednesday, 7:30 PM'},
    ]

    return render(
        request,
        'my_course_detail.html',
        {
            'active_page': 'courses',
            'course': course,
            'slug': slug,
            'module_outline': module_outline,
            'notes': notes,
            'video_lectures': video_lectures,
            'upcoming_meets': upcoming_meets,
        },
    )


def instructors(request):
    return render(request, 'instructors.html', {'active_page': 'instructors'})


def dashboard(request):
    return render(request, 'dashboard.html', {'active_page': 'dashboard'})


def _handle_admin_panel_action(request):
    action = request.POST.get('action')

    if action in {'promote_instructor', 'revoke_instructor'}:
        user = get_object_or_404(User, id=request.POST.get('user_id'))
        if user == request.user and action == 'revoke_instructor':
            messages.error(request, 'You cannot revoke your own instructor access from this panel.')
            return

        user.is_staff = action == 'promote_instructor'
        user.save(update_fields=['is_staff'])
        role_label = 'Instructor' if user.is_staff else 'Student'
        messages.success(request, f'{user.get_full_name() or user.username} is now marked as {role_label}.')


@staff_member_required(login_url='login')
def admin_panel(request):
    if request.method == 'POST':
        _handle_admin_panel_action(request)
        return redirect('admin_panel')

    instructors_list = InstructorProfile.objects.select_related('user').order_by('user__first_name', 'user__last_name')
    students_list = User.objects.filter(is_staff=False).annotate(total_enrollments=Count('enrollments')).order_by(
        '-date_joined'
    )

    context = {
        'active_page': 'admin_panel',
        'stats': {
            'total_courses': Course.objects.count(),
            'total_instructors': instructors_list.count(),
            'total_students': students_list.count(),
            'total_enrollments': Enrollment.objects.count(),
        },
        'instructors': instructors_list[:8],
        'students': students_list[:12],
    }
    return render(request, 'admin_panel.html', context)


@staff_member_required(login_url='login')
def admin_course_list(request):
    courses_qs = Course.objects.select_related('instructor').order_by('title')
    return render(
        request,
        'admin_courses.html',
        {'active_page': 'admin_panel', 'courses': courses_qs},
    )


@staff_member_required(login_url='login')
def admin_course_create(request):
    if request.method == 'POST':
        form = AdminCourseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Course created successfully.')
            return redirect('admin_courses')
    else:
        form = AdminCourseForm()

    return render(
        request,
        'admin_course_form.html',
        {'active_page': 'admin_panel', 'form': form, 'form_title': 'Add New Course', 'submit_label': 'Create Course'},
    )


@staff_member_required(login_url='login')
def admin_course_edit(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.method == 'POST':
        form = AdminCourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, 'Course updated successfully.')
            return redirect('admin_courses')
    else:
        form = AdminCourseForm(instance=course)

    return render(
        request,
        'admin_course_form.html',
        {'active_page': 'admin_panel', 'form': form, 'form_title': 'Edit Course', 'submit_label': 'Save Changes'},
    )


@staff_member_required(login_url='login')
def admin_course_delete(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.method == 'POST':
        course.delete()
        messages.success(request, 'Course deleted successfully.')
    return redirect('admin_courses')


@staff_member_required(login_url='login')
def admin_instructor_list(request):
    instructors_qs = InstructorProfile.objects.select_related('user').order_by('user__first_name', 'user__last_name')
    return render(
        request,
        'admin_instructors.html',
        {'active_page': 'admin_panel', 'instructors': instructors_qs},
    )


@staff_member_required(login_url='login')
def admin_instructor_create(request):
    if request.method == 'POST':
        form = AdminInstructorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Instructor added successfully.')
            return redirect('admin_instructors')
    else:
        form = AdminInstructorForm()

    return render(
        request,
        'admin_instructor_form.html',
        {'active_page': 'admin_panel', 'form': form, 'form_title': 'Add Instructor', 'submit_label': 'Create Instructor'},
    )


@staff_member_required(login_url='login')
def admin_instructor_edit(request, instructor_id):
    profile = get_object_or_404(InstructorProfile, id=instructor_id)
    if request.method == 'POST':
        form = AdminInstructorForm(request.POST, instance=profile, user_instance=profile.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Instructor details updated successfully.')
            return redirect('admin_instructors')
    else:
        form = AdminInstructorForm(instance=profile, user_instance=profile.user)

    return render(
        request,
        'admin_instructor_form.html',
        {'active_page': 'admin_panel', 'form': form, 'form_title': 'Edit Instructor', 'submit_label': 'Save Changes'},
    )


@staff_member_required(login_url='login')
def admin_instructor_delete(request, instructor_id):
    profile = get_object_or_404(InstructorProfile, id=instructor_id)
    if request.method == 'POST':
        if profile.user == request.user:
            messages.error(request, 'You cannot delete your own instructor account.')
            return redirect('admin_instructors')

        profile.user.delete()
        messages.success(request, 'Instructor deleted successfully.')
    return redirect('admin_instructors')


@staff_member_required(login_url='login')
def admin_student_list(request):
    students_qs = User.objects.filter(is_staff=False).annotate(total_enrollments=Count('enrollments')).order_by('-date_joined')
    return render(
        request,
        'admin_students.html',
        {'active_page': 'admin_panel', 'students': students_qs},
    )


@staff_member_required(login_url='login')
def admin_student_detail(request, student_id):
    student = get_object_or_404(User.objects.filter(is_staff=False), id=student_id)
    enrollments = Enrollment.objects.select_related('course').filter(user=student).order_by('-created_at')
    return render(
        request,
        'admin_student_detail.html',
        {'active_page': 'admin_panel', 'student': student, 'enrollments': enrollments},
    )


@staff_member_required(login_url='login')
def admin_student_deactivate(request, student_id):
    student = get_object_or_404(User.objects.filter(is_staff=False), id=student_id)
    if request.method == 'POST':
        student.is_active = not student.is_active
        student.save(update_fields=['is_active'])
        status_text = 'activated' if student.is_active else 'deactivated'
        messages.success(request, f'Student account {status_text} successfully.')
    return redirect('admin_students')


@staff_member_required(login_url='login')
def admin_student_delete(request, student_id):
    student = get_object_or_404(User.objects.filter(is_staff=False), id=student_id)
    if request.method == 'POST':
        student.delete()
        messages.success(request, 'Student account deleted successfully.')
    return redirect('admin_students')


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
        messages.success(request, f'Welcome back, {user.first_name or "Learner"}!')
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
        messages.success(request, 'Account created successfully. Welcome to LearnSphere!')
        return redirect('dashboard')

    return render(request, 'register.html', {'active_page': 'register'})


def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, 'You have been logged out successfully.')
    return redirect('home')
