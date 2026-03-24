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
            first_name='Admin',
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
            instructor=self.staff_user,
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


class AdminCourseCrudTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='owner@learnsphere.com',
            email='owner@learnsphere.com',
            password='StrongPass123!',
            is_staff=True,
            first_name='Owner',
        )
        self.second_instructor = User.objects.create_user(
            username='inst@learnsphere.com',
            email='inst@learnsphere.com',
            password='StrongPass123!',
            is_staff=True,
            first_name='Instructor',
        )
        self.client.login(username='owner@learnsphere.com', password='StrongPass123!')

        self.course = Course.objects.create(
            title='Existing Course',
            slug='existing-course',
            category='General',
            short_description='Existing short description',
            description='Existing long description',
            level=Course.Level.BEGINNER,
            duration_weeks=4,
            price='45.00',
            instructor=self.staff_user,
            is_published=True,
        )

    def test_admin_course_list_view(self):
        response = self.client.get(reverse('admin_courses'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Existing Course')

    def test_admin_can_add_course(self):
        payload = {
            'title': 'New Course',
            'description': 'This is a new course description',
            'instructor': self.second_instructor.id,
            'price': '99.99',
        }
        response = self.client.post(reverse('admin_course_create'), payload, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Course.objects.filter(title='New Course').exists())
        new_course = Course.objects.get(title='New Course')
        self.assertEqual(new_course.instructor, self.second_instructor)

    def test_admin_can_edit_course(self):
        payload = {
            'title': 'Existing Course Updated',
            'description': 'Updated description',
            'instructor': self.second_instructor.id,
            'price': '49.00',
        }
        response = self.client.post(reverse('admin_course_edit', args=[self.course.id]), payload, follow=True)
        self.assertEqual(response.status_code, 200)
        self.course.refresh_from_db()
        self.assertEqual(self.course.title, 'Existing Course Updated')
        self.assertEqual(str(self.course.price), '49.00')
        self.assertEqual(self.course.instructor, self.second_instructor)

    def test_admin_can_delete_course(self):
        response = self.client.post(reverse('admin_course_delete', args=[self.course.id]), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Course.objects.filter(id=self.course.id).exists())
