from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django.shortcuts import get_object_or_404
from courses.models import Course, Enrollment, Lesson, LessonProgress
from courses.api.serializers import (
    CourseSerializer, LessonSerializer,
    EnrollmentSerializer, QuizSerializer, ProfileSerializer, UserSerializer
)
from django.contrib.auth.models import User
from courses.payment import LemonSqueezyPaymentService
from django.utils import timezone
from courses.gamification import GamificationService









class CourseListView(generics.ListAPIView):
    """List all published courses"""
    queryset = Course.objects.filter(is_published=True)
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by category
        category = self.request.query__params.get('category')
        if category:
            queryset = queryset.filter(category__slug=category)

        # Filter by level
        level = self.request.query__params.get('level')
        if level:
            queryset = queryset.filter(level=level)

        # Search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(title__icontains=search) |
                models.Q(description__icontains=search)
            )        

        return queryset


class CourseDetailView(generics.RetrieveAPIView):
    """Get course details"""
    queryset = Course.objects.filter(is_published=True)
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def enroll_course_api(request, course_id):
    """API enddpoints for course enrollment """
    course = get_object_or_404(Course, id=course_id)

    if course.price > 0:
        # For paid courses, create payment checkout
        payment_service = LemonSqueezyPaymentService()
        checkout_url = payment_service.create_checkout(request, course)

        if checkout_url:
            return Response({
                'message': 'Redirect to checkout',
                'checkout_url': checkout_url
            })    
        else:
            return Response(
                {'error': 'Payment processing failed'},
                status=status.HTTP_400_BAD_REQUEST
            )
    else:
        # Free course - Enroll immediately
        enrollment, created = Enrollment.objects.get_or_create(
            student=request.user,
            course=course
        )    

        if created:
            return Response({
                'message': 'Already enrolled in this course'
            })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_enrollments_api(request):
    """API endpoints for user's enrollments"""
    enrollments = Enrollment.objects.filter(student=request.user)
    serializer = EnrollmentSerializer(enrollments, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def lesson_progress_api(request, lesson_id):
    """API endpoint for marking lesson progress"""
    lesson = get_object_or_404(Lesson, id=lesson_id)

    # Check if user is enrolled
    enrollment = Enrollment.objects.filter(
        student=request.user,
        course=lesson.module.course
    ).first()

    if not enrollment:
        return Response(
            {'error': 'Your are not enrolled in this course'},
            status=status.HTTP_403_FORBIDDEN
        )        
    
    progress, created = LessonProgress.objects.get_or_create(
        student=request.user,
        lesson=lesson
    )

    progress.completed = True
    progress.completed_at = timezone.now()
    progress.save()

    # Update enrollment progress
    enrollment.save()    # This will recalculate progress

    # Award XP for completing lesson
    GamificationService.award_xp(
        request.user,
        10,
        f'Completed lesson: {lesson.title}'
    )

    return Response({
        'message': 'Lesson marked as completed',
        'progress': enrollment.progress_percentage()
    })


# Auth API endpoints
@api_view(['POST'])
def reigister_api(request):
    """API endpoint for user registration"""
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        user.set_password(request.data['password'])
        user.save()

        # Create profile
        Profile.objects.create(user=user)

        return Response({
            'message': 'User created successfully',
            'user': serializer.data
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_profile_api(request):
    """API endpoint for updating user profiile"""
    profile = request.user.profile
    serializer = ProfileSerializer(profile, data=request.data, partial=True)
    
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)