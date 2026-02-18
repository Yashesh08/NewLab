from django.shortcuts import render


def home(request):
    return render(request, 'home.html', {'active_page': 'home'})


def courses(request):
    return render(request, 'courses.html', {'active_page': 'courses'})


def instructors(request):
    return render(request, 'instructors.html', {'active_page': 'instructors'})


def pricing(request):
    return render(request, 'pricing.html', {'active_page': 'pricing'})


def dashboard(request):
    return render(request, 'dashboard.html', {'active_page': 'dashboard'})
