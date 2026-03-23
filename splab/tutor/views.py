from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.db.models.functions import ExtractMonth
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .decorators import tutor_required
from .forms import AssignmentForm, CourseForm, LessonForm, SubmissionForm, SubmissionGradeForm, TutorProfileForm
from .models import Assignment, Course, Enrollment, Submission, Tutor


def _get_tutor(user):
    return get_object_or_404(Tutor, user=user)


@tutor_required
def tutor_dashboard(request):
    tutor = _get_tutor(request.user)
    courses = Course.objects.filter(tutor=tutor)
    enrollments = Enrollment.objects.filter(course__tutor=tutor)

    context = {
        'total_courses': courses.count(),
        'total_students': enrollments.values('student').distinct().count(),
        'active_enrollments': enrollments.filter(status=Enrollment.Status.ACTIVE).count(),
        'pending_assignments': Assignment.objects.filter(course__tutor=tutor, due_date__gte=timezone.now()).count(),
        'recent_courses': courses.order_by('-created_at')[:5],
    }
    return render(request, 'tutor/dashboard.html', context)


@tutor_required
def tutor_courses(request):
    tutor = _get_tutor(request.user)
    courses = Course.objects.filter(tutor=tutor).order_by('-created_at')
    return render(request, 'tutor/courses.html', {'courses': courses})


@tutor_required
def create_course(request):
    tutor = _get_tutor(request.user)
    form = CourseForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        course = form.save(commit=False)
        course.tutor = tutor
        course.save()
        messages.success(request, 'Course created successfully.')
        return redirect('tutor_courses')
    return render(request, 'tutor/create_course.html', {'form': form, 'is_edit': False})


@tutor_required
def edit_course(request, id):
    tutor = _get_tutor(request.user)
    course = get_object_or_404(Course, id=id, tutor=tutor)
    form = CourseForm(request.POST or None, request.FILES or None, instance=course)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Course updated successfully.')
        return redirect('tutor_courses')
    return render(request, 'tutor/create_course.html', {'form': form, 'is_edit': True})


@tutor_required
@require_POST
def delete_course(request, id):
    tutor = _get_tutor(request.user)
    course = get_object_or_404(Course, id=id, tutor=tutor)
    course.delete()
    messages.success(request, 'Course deleted successfully.')
    return redirect('tutor_courses')


@tutor_required
def tutor_students(request):
    tutor = _get_tutor(request.user)
    enrollments = Enrollment.objects.filter(course__tutor=tutor).select_related('student', 'course').order_by('-last_activity', '-enrolled_at')
    return render(request, 'tutor/students.html', {'enrollments': enrollments})


@tutor_required
def tutor_assignments(request):
    tutor = _get_tutor(request.user)
    assignment_form = AssignmentForm(request.POST or None, prefix='assignment')
    lesson_form = LessonForm(request.POST or None, request.FILES or None, prefix='lesson')
    assignment_form.fields['course'].queryset = Course.objects.filter(tutor=tutor)
    lesson_form.fields['course'].queryset = Course.objects.filter(tutor=tutor)

    if request.method == 'POST':
        if 'create_assignment' in request.POST and assignment_form.is_valid():
            assignment_form.save()
            messages.success(request, 'Assignment created.')
            return redirect('tutor_assignments')
        if 'create_lesson' in request.POST and lesson_form.is_valid():
            lesson_form.save()
            messages.success(request, 'Lesson added.')
            return redirect('tutor_assignments')

    assignments = Assignment.objects.filter(course__tutor=tutor).prefetch_related('submissions__student', 'course')
    return render(
        request,
        'tutor/assignments.html',
        {'assignment_form': assignment_form, 'lesson_form': lesson_form, 'assignments': assignments},
    )


@login_required
@require_POST
def submit_assignment(request, id):
    assignment = get_object_or_404(Assignment, id=id)

    if not Enrollment.objects.filter(course=assignment.course, student=request.user).exists():
        messages.error(request, 'You are not enrolled in this course.')
        return redirect('dashboard')

    form = SubmissionForm(request.POST, request.FILES)
    if form.is_valid():
        Submission.objects.update_or_create(
            assignment=assignment,
            student=request.user,
            defaults={'file': form.cleaned_data['file']},
        )
        messages.success(request, 'Assignment submitted successfully.')
    else:
        messages.error(request, 'Please upload a valid submission file.')

    return redirect('dashboard')


@tutor_required
@require_POST
def grade_submission(request, id):
    tutor = _get_tutor(request.user)
    submission = get_object_or_404(Submission, id=id, assignment__course__tutor=tutor)
    form = SubmissionGradeForm(request.POST, instance=submission)
    if form.is_valid():
        form.save()
        messages.success(request, 'Submission graded.')
    else:
        messages.error(request, 'Invalid grade value.')
    return redirect('tutor_assignments')


@tutor_required
def tutor_analytics(request):
    tutor = _get_tutor(request.user)
    monthly = (
        Enrollment.objects.filter(course__tutor=tutor)
        .annotate(month=ExtractMonth('enrolled_at'))
        .values('month')
        .annotate(total=Count('id'))
        .order_by('month')
    )
    month_map = {i: 0 for i in range(1, 13)}
    for row in monthly:
        if row['month']:
            month_map[row['month']] = row['total']

    assignments = Assignment.objects.filter(course__tutor=tutor)
    submissions_count = Submission.objects.filter(assignment__in=assignments).count()
    completion_count = Enrollment.objects.filter(course__tutor=tutor, status=Enrollment.Status.COMPLETED).count()
    enroll_count = Enrollment.objects.filter(course__tutor=tutor).count()
    completion_rate = round((completion_count / enroll_count) * 100, 2) if enroll_count else 0

    context = {
        'month_labels': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        'monthly_enrollments': [month_map[i] for i in range(1, 13)],
        'assignment_submissions': submissions_count,
        'course_completion_rate': completion_rate,
        'completion_remaining': max(0, 100 - completion_rate),
    }
    return render(request, 'tutor/analytics.html', context)


@tutor_required
def tutor_profile(request):
    tutor = _get_tutor(request.user)
    form = TutorProfileForm(request.POST or None, request.FILES or None, instance=tutor)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('tutor_profile')
    return render(request, 'tutor/profile.html', {'form': form})
