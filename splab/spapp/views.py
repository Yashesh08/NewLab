from django.http import Http404
from django.shortcuts import render

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


def home(request):
    return render(request, 'home.html', {'active_page': 'home'})


def courses(request):
    courses_list = [{'slug': slug, **course} for slug, course in COURSE_CATALOG.items()]
    return render(
        request,
        'courses.html',
        {'active_page': 'courses', 'courses': courses_list},
    )


def course_detail(request, slug):
    course = COURSE_CATALOG.get(slug)
    if not course:
        raise Http404('Course not found')
    return render(
        request,
        'course_detail.html',
        {'active_page': 'courses', 'course': course, 'slug': slug},
    )


def instructors(request):
    return render(request, 'instructors.html', {'active_page': 'instructors'})


def dashboard(request):
    return render(request, 'dashboard.html', {'active_page': 'dashboard'})
