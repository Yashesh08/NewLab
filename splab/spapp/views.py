from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import Http404
from django.shortcuts import redirect, render

COURSE_CATALOG = {
    'full-stack-javascript-bootcamp': {
        'title': 'Full-Stack JavaScript Bootcamp',
        'category': 'Development',
        'level': 'Beginner',
        'duration': '10 weeks',
        'price': '$49',
        'description': 'Learn HTML, CSS, JavaScript, Node.js, and MongoDB by building complete end-to-end applications.'
    },
    'react-for-intermediate-developers': {
        'title': 'React for Intermediate Developers',
        'category': 'Development',
        'level': 'Intermediate',
        'duration': '6 weeks',
        'price': '$59',
        'description': 'Master hooks, routing, performance optimization, and reusable component architecture in real projects.'
    },
    'figma-ui-design-workshop': {
        'title': 'Figma UI Design Workshop',
        'category': 'Design',
        'level': 'Beginner',
        'duration': '4 weeks',
        'price': '$39',
        'description': 'Build polished user interfaces in Figma with practical workflows, components, and design handoff.'
    },
    'advanced-product-design-systems': {
        'title': 'Advanced Product Design Systems',
        'category': 'Design',
        'level': 'Advanced',
        'duration': '8 weeks',
        'price': '$69',
        'description': 'Create scalable design systems and governance practices for high-growth product teams.'
    },
    'growth-marketing-seo': {
        'title': 'Growth Marketing & SEO',
        'category': 'Marketing',
        'level': 'Intermediate',
        'duration': '5 weeks',
        'price': '$44',
        'description': 'Learn acquisition channels, SEO fundamentals, and conversion experiments to grow product adoption.'
    },
    'data-analytics-with-python': {
        'title': 'Data Analytics with Python',
        'category': 'Data',
        'level': 'Beginner',
        'duration': '7 weeks',
        'price': '$54',
        'description': 'Analyze and visualize datasets using Python, pandas, and practical business intelligence workflows.'
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


def add_video_lecture(request):
    if not request.user.is_authenticated:
        messages.error(request, 'Please log in to upload a lecture.')
        return redirect('login')

    lecture_data = None
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        course_name = request.POST.get('course_name', '').strip()
        video_url = request.POST.get('video_url', '').strip()
        duration = request.POST.get('duration', '').strip()
        description = request.POST.get('description', '').strip()

        lecture_data = {
            'title': title,
            'course_name': course_name,
            'video_url': video_url,
            'duration': duration,
            'description': description,
        }

        if not all([title, course_name, video_url, duration, description]):
            messages.error(request, 'Please fill in all lecture details before submitting.')
        else:
            messages.success(request, f'Lecture "{title}" has been added successfully.')

    return render(
        request,
        'add_video_lecture.html',
        {'active_page': 'add_video_lecture', 'lecture': lecture_data},
    )


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
