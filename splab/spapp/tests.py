from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Course, Enrollment, InstructorProfile


class AdminPanelViewTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='admin@learnsphere.com',
            email='admin@learnsphere.com',
            password='StrongPass123!',
            is_staff=True,
            first_name='Admin',
        )
        self.instructor_profile = InstructorProfile.objects.create(
            user=self.staff_user,
            expertise='Web Development',
            experience='6 years',
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
        self.assertEqual(response.context['stats']['total_instructors'], 1)
        self.assertEqual(response.context['stats']['total_students'], 1)
        self.assertEqual(response.context['stats']['total_enrollments'], 1)


class AdminCourseCrudTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='owner@learnsphere.com',
            email='owner@learnsphere.com',
            password='StrongPass123!',
            is_staff=True,
            first_name='Owner',
        )
        InstructorProfile.objects.create(user=self.staff_user, expertise='Backend', experience='5 years')
        self.second_instructor = User.objects.create_user(
            username='inst@learnsphere.com',
            email='inst@learnsphere.com',
            password='StrongPass123!',
            is_staff=True,
            first_name='Instructor',
        )
        InstructorProfile.objects.create(user=self.second_instructor, expertise='Frontend', experience='4 years')
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

    def test_admin_can_delete_course(self):
        response = self.client.post(reverse('admin_course_delete', args=[self.course.id]), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Course.objects.filter(id=self.course.id).exists())


class AdminInstructorCrudTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='admin2@learnsphere.com',
            email='admin2@learnsphere.com',
            password='StrongPass123!',
            is_staff=True,
            first_name='Primary',
        )
        self.profile = InstructorProfile.objects.create(
            user=self.staff_user,
            expertise='Data Science',
            experience='7 years',
        )
        self.client.login(username='admin2@learnsphere.com', password='StrongPass123!')

    def test_admin_instructor_list_view(self):
        response = self.client.get(reverse('admin_instructors'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Data Science')

    def test_admin_can_create_instructor(self):
        payload = {
            'first_name': 'Nina',
            'last_name': 'Patel',
            'email': 'nina@learnsphere.com',
            'password': 'StrongPass123!',
            'expertise': 'Product Design',
            'experience': '8 years',
        }
        response = self.client.post(reverse('admin_instructor_create'), payload, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(InstructorProfile.objects.filter(user__email='nina@learnsphere.com').exists())

    def test_admin_can_edit_instructor(self):
        payload = {
            'first_name': 'Primary',
            'last_name': 'Admin',
            'email': 'admin2@learnsphere.com',
            'password': '',
            'expertise': 'AI Engineering',
            'experience': '9 years',
        }
        response = self.client.post(reverse('admin_instructor_edit', args=[self.profile.id]), payload, follow=True)
        self.assertEqual(response.status_code, 200)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.expertise, 'AI Engineering')
        self.assertEqual(self.profile.experience, '9 years')

    def test_admin_can_delete_instructor(self):
        other_user = User.objects.create_user(
            username='delete@learnsphere.com',
            email='delete@learnsphere.com',
            password='StrongPass123!',
            is_staff=True,
        )
        other_profile = InstructorProfile.objects.create(
            user=other_user,
            expertise='Cloud',
            experience='3 years',
        )
        response = self.client.post(reverse('admin_instructor_delete', args=[other_profile.id]), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(InstructorProfile.objects.filter(id=other_profile.id).exists())


class AdminStudentManagementTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='staff@learnsphere.com',
            email='staff@learnsphere.com',
            password='StrongPass123!',
            is_staff=True,
        )
        self.student_user = User.objects.create_user(
            username='learner@learnsphere.com',
            email='learner@learnsphere.com',
            password='StrongPass123!',
            first_name='Learner',
        )
        self.course = Course.objects.create(
            title='Student Testing Course',
            slug='student-testing-course',
            category='General',
            short_description='short',
            description='desc',
            level=Course.Level.BEGINNER,
            duration_weeks=4,
            price='12.00',
            is_published=True,
        )
        Enrollment.objects.create(user=self.student_user, course=self.course, status=Enrollment.Status.ACTIVE)
        self.client.login(username='staff@learnsphere.com', password='StrongPass123!')

    def test_admin_student_list_view(self):
        response = self.client.get(reverse('admin_students'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'learner@learnsphere.com')

    def test_admin_student_detail_view(self):
        response = self.client.get(reverse('admin_student_detail', args=[self.student_user.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Student Testing Course')

    def test_admin_can_deactivate_and_reactivate_student(self):
        deactivate_response = self.client.post(reverse('admin_student_deactivate', args=[self.student_user.id]), follow=True)
        self.assertEqual(deactivate_response.status_code, 200)
        self.student_user.refresh_from_db()
        self.assertFalse(self.student_user.is_active)

        activate_response = self.client.post(reverse('admin_student_deactivate', args=[self.student_user.id]), follow=True)
        self.assertEqual(activate_response.status_code, 200)
        self.student_user.refresh_from_db()
        self.assertTrue(self.student_user.is_active)

    def test_admin_can_delete_student(self):
        response = self.client.post(reverse('admin_student_delete', args=[self.student_user.id]), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(id=self.student_user.id).exists())


class AdminEnrollmentViewTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='staff2@learnsphere.com',
            email='staff2@learnsphere.com',
            password='StrongPass123!',
            is_staff=True,
        )
        self.student_user = User.objects.create_user(
            username='enrollstudent@learnsphere.com',
            email='enrollstudent@learnsphere.com',
            password='StrongPass123!',
            first_name='Enroll',
            last_name='Student',
        )
        self.course = Course.objects.create(
            title='Enrollment Course',
            slug='enrollment-course',
            category='General',
            short_description='short',
            description='desc',
            level=Course.Level.BEGINNER,
            duration_weeks=4,
            price='30.00',
            is_published=True,
        )
        Enrollment.objects.create(user=self.student_user, course=self.course, status=Enrollment.Status.ACTIVE)
        self.client.login(username='staff2@learnsphere.com', password='StrongPass123!')

    def test_admin_enrollment_list_view(self):
        response = self.client.get(reverse('admin_enrollments'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Enroll Student')
        self.assertContains(response, 'Enrollment Course')
