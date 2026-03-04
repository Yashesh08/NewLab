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

TUTOR_COURSE_SLUGS = [
    'full-stack-javascript-bootcamp',
    'react-for-intermediate-developers',
    'data-analytics-with-python',
]


def get_tutor_workspace(request):
    workspace = request.session.get('tutor_workspace')
    if not workspace:
        workspace = {
            'lectures': [],
            'sessions': [],
            'assignments': [],
            'announcements': [],
        }
    return workspace


def save_tutor_workspace(request, workspace):
    request.session['tutor_workspace'] = workspace
    request.session.modified = True


def get_course(slug):
    course = COURSE_CATALOG.get(slug)
    if not course:
        raise Http404('Course not found')
    return course


def is_tutor(request):
    return request.session.get('user_role') == 'tutor'


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
    if is_tutor(request):
        return redirect('tutor_dashboard')
    return render(request, 'dashboard.html', {'active_page': 'dashboard'})


def tutor_dashboard(request):
    if not request.user.is_authenticated:
        messages.error(request, 'Please log in to continue.')
        return redirect('login')

    if not is_tutor(request):
        messages.error(request, 'Tutor dashboard is only available for tutor login.')
        return redirect('dashboard')

    tutor_courses = [
        {'slug': slug, **COURSE_CATALOG[slug]}
        for slug in TUTOR_COURSE_SLUGS
        if slug in COURSE_CATALOG
    ]

    workspace = get_tutor_workspace(request)
    dashboard_stats = {
        'lectures_count': len(workspace['lectures']),
        'sessions_count': len(workspace['sessions']),
        'assignments_count': len(workspace['assignments']),
        'announcements_count': len(workspace['announcements']),
    }

    recent_activity = (
        [{'type': 'Lecture', 'title': item['title'], 'course_name': item['course_name']} for item in workspace['lectures']]
        + [{'type': 'Live Session', 'title': item['topic'], 'course_name': item['course_name']} for item in workspace['sessions']]
        + [{'type': 'Assignment', 'title': item['title'], 'course_name': item['course_name']} for item in workspace['assignments']]
        + [{'type': 'Announcement', 'title': item['title'], 'course_name': item['course_name']} for item in workspace['announcements']]
    )[::-1][:6]

    return render(
        request,
        'tutor_dashboard.html',
        {
            'active_page': 'tutor_dashboard',
            'tutor_courses': tutor_courses,
            'dashboard_stats': dashboard_stats,
            'recent_activity': recent_activity,
        },
    )


def add_video_lecture(request):
    if not request.user.is_authenticated:
        messages.error(request, 'Please log in to upload a lecture.')
        return redirect('login')

    if not is_tutor(request):
        messages.error(request, 'Only tutors can add video lectures.')
        return redirect('dashboard')

    workspace = get_tutor_workspace(request)
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
            workspace['lectures'].append(lecture_data)
            save_tutor_workspace(request, workspace)
            messages.success(request, f'Lecture "{title}" has been added successfully.')

    return render(
        request,
        'add_video_lecture.html',
        {
            'active_page': 'add_video_lecture',
            'lecture': lecture_data,
            'recent_lectures': workspace['lectures'][::-1][:5],
        },
    )


def add_live_session(request):
    if not request.user.is_authenticated:
        messages.error(request, 'Please log in to schedule a session.')
        return redirect('login')

    if not is_tutor(request):
        messages.error(request, 'Only tutors can schedule live sessions.')
        return redirect('dashboard')

    workspace = get_tutor_workspace(request)
    session_data = None
    if request.method == 'POST':
        topic = request.POST.get('topic', '').strip()
        course_name = request.POST.get('course_name', '').strip()
        session_date = request.POST.get('session_date', '').strip()
        session_time = request.POST.get('session_time', '').strip()
        meet_link = request.POST.get('meet_link', '').strip()

        session_data = {
            'topic': topic,
            'course_name': course_name,
            'session_date': session_date,
            'session_time': session_time,
            'meet_link': meet_link,
        }

        if not all([topic, course_name, session_date, session_time, meet_link]):
            messages.error(request, 'Please complete all session details before publishing.')
        else:
            workspace['sessions'].append(session_data)
            save_tutor_workspace(request, workspace)
            messages.success(request, f'Live session "{topic}" has been published.')

    return render(
        request,
        'add_live_session.html',
        {
            'active_page': 'add_live_session',
            'session_info': session_data,
            'upcoming_sessions': workspace['sessions'][::-1][:5],
        },
    )


def add_assignment(request):
    if not request.user.is_authenticated:
        messages.error(request, 'Please log in to create assignments.')
        return redirect('login')

    if not is_tutor(request):
        messages.error(request, 'Only tutors can create assignments.')
        return redirect('dashboard')

    workspace = get_tutor_workspace(request)
    assignment_data = None

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        course_name = request.POST.get('course_name', '').strip()
        due_date = request.POST.get('due_date', '').strip()
        max_marks = request.POST.get('max_marks', '').strip()
        instructions = request.POST.get('instructions', '').strip()

        assignment_data = {
            'title': title,
            'course_name': course_name,
            'due_date': due_date,
            'max_marks': max_marks,
            'instructions': instructions,
        }

        if not all([title, course_name, due_date, max_marks, instructions]):
            messages.error(request, 'Please complete all assignment details.')
        else:
            workspace['assignments'].append(assignment_data)
            save_tutor_workspace(request, workspace)
            messages.success(request, f'Assignment "{title}" has been created.')

    return render(
        request,
        'add_assignment.html',
        {
            'active_page': 'add_assignment',
            'assignment': assignment_data,
            'recent_assignments': workspace['assignments'][::-1][:5],
        },
    )


def tutor_announcements(request):
    if not request.user.is_authenticated:
        messages.error(request, 'Please log in to post announcements.')
        return redirect('login')

    if not is_tutor(request):
        messages.error(request, 'Only tutors can post announcements.')
        return redirect('dashboard')

    workspace = get_tutor_workspace(request)
    announcement_data = None

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        course_name = request.POST.get('course_name', '').strip()
        message_text = request.POST.get('message', '').strip()
        priority = request.POST.get('priority', '').strip()

        announcement_data = {
            'title': title,
            'course_name': course_name,
            'message': message_text,
            'priority': priority,
        }

        if not all([title, course_name, message_text, priority]):
            messages.error(request, 'Please complete all announcement details.')
        else:
            workspace['announcements'].append(announcement_data)
            save_tutor_workspace(request, workspace)
            messages.success(request, f'Announcement "{title}" has been posted.')

    return render(
        request,
        'tutor_announcements.html',
        {
            'active_page': 'tutor_announcements',
            'announcement': announcement_data,
            'recent_announcements': workspace['announcements'][::-1][:5],
        },
    )


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        user_role = request.POST.get('user_role', '').strip().lower()

        if not email or not password:
            messages.error(request, 'Please enter both email and password.')
            return render(request, 'login.html', {'active_page': 'login', 'email': email, 'user_role': user_role})

        if user_role not in {'student', 'tutor'}:
            messages.error(request, 'Please select whether you are logging in as Student or Tutor.')
            return render(request, 'login.html', {'active_page': 'login', 'email': email})

        user = authenticate(request, username=email, password=password)
        if user is None:
            messages.error(request, 'Invalid credentials. Please try again.')
            return render(request, 'login.html', {'active_page': 'login', 'email': email, 'user_role': user_role})

        login(request, user)
        request.session['user_role'] = user_role
        messages.success(request, f'Welcome back, {user.first_name or "Learner"}!')
        if user_role == 'tutor':
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
        request.session['user_role'] = 'student'
        messages.success(request, 'Account created successfully. Welcome to LearnSphere!')
        return redirect('dashboard')

    return render(request, 'register.html', {'active_page': 'register'})


def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, 'You have been logged out successfully.')
    return redirect('home')
