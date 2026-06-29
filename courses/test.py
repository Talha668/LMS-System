# from django.test import TestCase, Client
# from django.contrib.auth import get_user_model
# from django.urls import reverse
# from .models import Course



# User = get_user_model


# class CourseMiddleTest(TestCase):
#     "Test case to check if it will run the test"
#     def setUp(self):
#         self.user = User.objects.create_user(
#             username='testuser',
#             password='passtest123',
#         )
#         self.course = Course.objects.create(
#             title='Test Course',
#             description='Test course for quiz',
#             instructor=self.user
#         )

#         def test_couse_creation(self):
#             "Test that the couse is created correctly"
#             self.assertEqual(self.course.title, 'Test Course')
#             self.assertEqual(self.course.description, 'Test course for quiz')
#             self.assertEqual(self.course.instructor.username, 'testuser')

#         def test_course_str_method(self):
#             "Test the string representation of the course"
#             self.assertEqual(str(self.course), 'Test Course')

#         def test_couse_has_created_at(self):
#             "Test that created_at is auto-set"
#             self.assertIsNone(self.course.created_at)

#         def test_course_is_updated_at(self):
#             "Test that updated_at is auto-set"
#             self.assertIsNone(self.course.updated_at)


# class CourseViewsTest(TestCase):
#     def setUp(self):
#         self.client = Client()
#         self.user = User.objects.create_user(
#             username='testuser',
#             password='testpass123'
#         )
#         self.course = Course.objects.create(
#             title='Test Course',
#             description='Test Description',
#             instructor=self.user
#         )

#     def test_course_list_view(self):
#         "Test that course list page loads"
#         response = self.client.get(reverse('course_list'))
#         self.assertEqual(response.status_code, 200)
#         self.assertTemplateUsed(response, 'course/course_list.html')

#     def test_course_detail_view(self):
#         "Test that course detail page loads"
#         response = self.client.get(reverse('course_detail', args=[self.course.id]))
#         self.assertEqual(response.status_code, 200)
#         self.assertContains(response, 'Test Course')


# class UserModelTest(TestCase):
#     def test_create_user(self):
#         "Test creating a regular user"
#         user = User.objects.create_user(
#             username='regularuser',
#             email='regular@example.com',
#             password='pass123'
#         )
#         self.assertEqual(user.username, 'regualaruser')
#         self.assertTrue(user.check_password('pass123'))
#         self.assertTrue(user.is_active)
#         self.assertFalse(user.is_staff)
#         self.assertFalse(user.is_superuser)

#     def test_create_superuser(self):
#         "Test creating a superuser"
#         admin = User.objects.create_superuser(
#             username='admin',
#             email='admin@example.com',
#             password='adminpass123'
#         )    
#         self.assertTrue(admin.is_staff)
#         self.assertTrue(admin.is_superuser)

#     # Test that will intentionally fail to check the pipeline
#     # def test_intentional_failure(self):
#         # "This test will fail intentionally"
#         # self.assertEqual(1, 2)    # This will fail       