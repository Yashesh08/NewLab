from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse


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

        admin_response = self.client.get(reverse('admin_panel'), follow=True)
        instructor_response = self.client.get(reverse('instructor_panel'))

        self.assertRedirects(admin_response, reverse('dashboard'))
        self.assertContains(admin_response, 'Unauthorized: only admins can access admin dashboard pages.')
        self.assertRedirects(instructor_response, reverse('home'))

    def test_instructor_user_cannot_access_admin_routes(self):
        self.client.login(username=self.instructor_user.username, password=self.password)

        admin_response = self.client.get(reverse('admin_panel'), follow=True)

        self.assertRedirects(admin_response, reverse('dashboard'))
        self.assertContains(admin_response, 'Unauthorized: only admins can access admin dashboard pages.')

    def test_anonymous_user_redirected_to_login_for_admin_routes(self):
        response = self.client.get(reverse('admin_panel'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('admin_panel')}")
