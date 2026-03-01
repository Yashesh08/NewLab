from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import Http404
from django.shortcuts import redirect, render

HOME_PARTNERS = ['Google', 'Microsoft', 'Amazon', 'Adobe', 'IBM']

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
    courses_list = [{'slug': slug, **course} for slug, course in COURSE_CATALOG.items()]
    featured_paths = courses_list[:3]

    badge_class_by_level = {
        'Beginner': 'success',
        'Intermediate': 'warning',
        'Advanced': 'danger',
    }
    for index, course in enumerate(featured_paths, start=1):
        course['badge_text'] = f"{course['level']} Track"
        course['badge_class'] = badge_class_by_level.get(course['level'], 'warning')
        course['projects'] = 4 + index * 2

    category_count = len({course['category'] for course in courses_list})
    average_price = round(
        sum(int(course['price'].replace('$', '')) for course in courses_list) / max(len(courses_list), 1),
        1,
    )

    learning_week = [
        f'✅ Complete "{featured_paths[0]["title"]}" lesson plan' if featured_paths else '✅ Complete your first lesson',
        '📝 Submit Assignment: Build a responsive dashboard',
        '🎥 Live Mentor Session: Saturday, 7:00 PM',
        f'🏆 Milestone unlocked: {len(PURCHASED_COURSE_SLUGS)} enrolled courses',
    ]

    context = {
        'active_page': 'home',
        'hero_badge': 'New Cohort Starts 15th June',
        'hero_title': 'Build job-ready skills with a complete learning platform.',
        'hero_subtitle': (
            'LearnSphere combines structured learning paths, mentor support, hands-on assignments, '
            'and placement-focused prep so you can turn learning into real career growth.'
        ),
        'hero_metrics': [
            {'value': '40k+', 'label': 'Learners enrolled'},
            {'value': f'{len(courses_list)}+', 'label': 'Industry-ready courses'},
            {'value': f'${average_price}', 'label': 'Average course fee'},
            {'value': f'{category_count}', 'label': 'Learning categories'},
        ],
        'learning_week': learning_week,
        'partners': HOME_PARTNERS,
        'featured_paths': featured_paths,
        'features': HOME_FEATURES,
    }

    return render(request, 'home.html', context)


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
