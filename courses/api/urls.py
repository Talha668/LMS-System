from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views





urlPatterns = [
    # Auth
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', views.reigister_api, name='api_register'),
    # Courses
    path('courses/', views.CourseListView.as_view(), name='api_courses'),
    path('courses/<int:pk>/', views.CourseDetailView.as_views, name='api_course_detail'),
    # Enrollment
    path('courses/<int:course_id>/enroll/', views.enroll_course_api, name='api_enroll'),
    path('my-enrollments/', views.my_enrollments_api, name='api_my_enrollments'),
    # Progress
    path('lesson/<int:lesson_id>/progress/', views.lesson_progress_api, name='api_lesson_progress'),
    # Profile
    path('profile/update', views.update_profile_api, name='api_update_profile'),     
]