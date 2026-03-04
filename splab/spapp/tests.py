from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Course, Enrollment


class AdminPanelViewTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='admin@learnsphere.com',
            email='admin@learnsphere.com',
            password='StrongPass123!',
            is_staff=True,
        )
        self.student_user = User.objects.create_user(
            username='student@learnsphere.com',
            email='student@learnsphere.com',
            password='StrongPass123!',
            first_name='Student',
        )
        self.course = Course.objects.create(
            title='Python Essentials',
            slug='python-essentials',
            category='Development',
            short_description='Intro to python',
            description='Longer description',
            level=Course.Level.BEGINNER,
            duration_weeks=4,
            price='29.00',
            is_published=True,
        )
        Enrollment.objects.create(user=self.student_user, course=self.course, status=Enrollment.Status.ACTIVE)

    def test_admin_panel_redirects_non_staff_user(self):
        self.client.login(username='student@learnsphere.com', password='StrongPass123!')
        response = self.client.get(reverse('admin_panel'))
        self.assertEqual(response.status_code, 302)

    def test_admin_panel_access_for_staff_user(self):
        self.client.login(username='admin@learnsphere.com', password='StrongPass123!')
        response = self.client.get(reverse('admin_panel'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin_panel.html')
        self.assertEqual(response.context['stats']['total_courses'], 1)
        self.assertEqual(response.context['stats']['total_enrollments'], 1)
        self.assertEqual(response.context['stats']['total_instructors'], 1)

    def test_admin_panel_can_unpublish_course(self):
        self.client.login(username='admin@learnsphere.com', password='StrongPass123!')
        response = self.client.post(
            reverse('admin_panel'),
            {'action': 'unpublish_course', 'course_id': self.course.id},
            follow=True,
        )
        self.course.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.course.is_published)

    def test_admin_panel_can_promote_student_to_instructor(self):
        self.client.login(username='admin@learnsphere.com', password='StrongPass123!')
        response = self.client.post(
            reverse('admin_panel'),
            {'action': 'promote_instructor', 'user_id': self.student_user.id},
            follow=True,
        )
        self.student_user.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.student_user.is_staff)
