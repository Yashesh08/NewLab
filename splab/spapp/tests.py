from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Assignment, Course, Enrollment, LiveMeet


class RoleAccessTests(TestCase):
    def setUp(self):
        self.password = 'testpass123'
        self.admin_user = User.objects.create_user(
            username='admin@example.com',
            email='admin@example.com',
            password=self.password,
            is_staff=True,
        )
        self.instructor_user = User.objects.create_user(
            username='inst@example.com',
            email='inst@example.com',
            password=self.password,
            first_name='Inst',
            last_name='Ructor',
        )
        self.regular_user = User.objects.create_user(
            username='user@example.com',
            email='user@example.com',
            password=self.password,
        )
        instructors_group, _ = Group.objects.get_or_create(name='Instructor')
        self.instructor_user.groups.add(instructors_group)

    def test_admin_user_redirects_to_admin_panel_after_login(self):
        response = self.client.post(
            reverse('login'),
            {'email': self.admin_user.username, 'password': self.password},
        )
        self.assertRedirects(response, reverse('admin_panel'))

    def test_instructor_user_redirects_to_instructor_panel_after_login(self):
        response = self.client.post(
            reverse('login'),
            {'email': self.instructor_user.username, 'password': self.password},
        )
        self.assertRedirects(response, reverse('instructor_panel'))

    def test_regular_user_redirects_to_dashboard_after_login(self):
        response = self.client.post(
            reverse('login'),
            {'email': self.regular_user.username, 'password': self.password},
        )
        self.assertRedirects(response, reverse('dashboard'))

    def test_regular_user_cannot_access_admin_or_instructor_panel(self):
        self.client.login(username=self.regular_user.username, password=self.password)

        admin_response = self.client.get(reverse('admin_panel'))
        instructor_response = self.client.get(reverse('instructor_panel'))

        self.assertRedirects(admin_response, reverse('home'))
        self.assertRedirects(instructor_response, reverse('home'))


class DashboardPlannerTests(TestCase):
    def setUp(self):
        self.password = 'testpass123'
        self.user = User.objects.create_user(
            username='learner@example.com',
            email='learner@example.com',
            password=self.password,
        )
        self.course = Course.objects.create(
            title='Data Science Bootcamp',
            slug='data-science-bootcamp',
            category='Data',
            short_description='Learn practical data science.',
            description='A complete data science track.',
            level=Course.Level.BEGINNER,
            duration_weeks=8,
            price=99.99,
            is_published=True,
        )
        Enrollment.objects.create(user=self.user, course=self.course, progress_percent=25)

    def test_dashboard_includes_planner_items_for_upcoming_events(self):
        Assignment.objects.create(
            course=self.course,
            title='Week 1 Assignment',
            instructions='Submit notebook',
            due_at=timezone.now() + timezone.timedelta(days=2),
            max_score=100,
        )
        LiveMeet.objects.create(
            course=self.course,
            topic='Doubt Solving Session',
            scheduled_at=timezone.now() + timezone.timedelta(days=1),
            meeting_url='https://example.com/live-session',
            duration_minutes=45,
        )

        self.client.login(username=self.user.username, password=self.password)
        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Smart Study Planner')
        self.assertEqual(len(response.context['planner_items']), 2)
        self.assertEqual(response.context['high_priority_count'], 2)


class CoursesFilteringTests(TestCase):
    def setUp(self):
        Course.objects.create(
            title='Python for Beginners',
            slug='python-for-beginners',
            category='Development',
            short_description='Start coding with Python.',
            description='Hands-on Python foundations.',
            level=Course.Level.BEGINNER,
            duration_weeks=4,
            price=39.00,
            is_published=True,
        )
        Course.objects.create(
            title='Advanced Data Pipelines',
            slug='advanced-data-pipelines',
            category='Data',
            short_description='Build modern data pipelines.',
            description='ETL, orchestration, and reliability.',
            level=Course.Level.ADVANCED,
            duration_weeks=12,
            price=89.00,
            is_published=True,
        )
        Course.objects.create(
            title='Product Design Basics',
            slug='product-design-basics',
            category='Design',
            short_description='Learn design fundamentals.',
            description='UI/UX core principles.',
            level=Course.Level.INTERMEDIATE,
            duration_weeks=6,
            price=59.00,
            is_published=True,
        )

    def test_courses_page_applies_combined_filters(self):
        response = self.client.get(
            reverse('courses'),
            {
                'q': 'data',
                'category': 'Data',
                'level': Course.Level.ADVANCED,
                'max_price': '90',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Advanced Data Pipelines')
        self.assertNotContains(response, 'Python for Beginners')
        self.assertEqual(response.context['result_count'], 1)

    def test_courses_page_sorts_by_price_high_to_low(self):
        response = self.client.get(
            reverse('courses'),
            {'sort': 'price_high_low'},
        )

        self.assertEqual(response.status_code, 200)
        course_titles = [course['title'] for course in response.context['courses']]
        self.assertEqual(
            course_titles,
            ['Advanced Data Pipelines', 'Product Design Basics', 'Python for Beginners'],
        )
