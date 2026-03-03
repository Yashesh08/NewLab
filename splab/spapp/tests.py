from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class TutorRoleFlowTests(TestCase):
    def setUp(self):
        self.email = 'mentor@example.com'
        self.password = 'StrongPass123'
        self.user = User.objects.create_user(
            username=self.email,
            email=self.email,
            password=self.password,
            first_name='Mentor',
        )

    def test_tutor_login_redirects_to_tutor_dashboard(self):
        response = self.client.post(
            reverse('login'),
            {
                'email': self.email,
                'password': self.password,
                'user_role': 'tutor',
            },
        )

        self.assertRedirects(response, reverse('tutor_dashboard'))
        session = self.client.session
        self.assertEqual(session.get('user_role'), 'tutor')

    def test_student_cannot_open_tutor_pages(self):
        self.client.post(
            reverse('login'),
            {
                'email': self.email,
                'password': self.password,
                'user_role': 'student',
            },
        )

        response = self.client.get(reverse('add_video_lecture'))
        self.assertRedirects(response, reverse('dashboard'))

    def test_tutor_can_open_live_session_page(self):
        self.client.post(
            reverse('login'),
            {
                'email': self.email,
                'password': self.password,
                'user_role': 'tutor',
            },
        )

        response = self.client.get(reverse('add_live_session'))
        self.assertEqual(response.status_code, 200)
