from django.db.models import Count, Avg, Q, Sum
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone
from datetime import timedelta
from .models import (
    Course, Enrollment, LessonProgress, QuizAttempt, User, Lesson, DiscussionReply, DiscussionThread, Quiz
)
from django.contrib.auth.models import User









class AnalyticsService:
    """Service for collecting and analyzing platform data"""
    @staticmethod
    def get_user_progress(user):
        """get comprehensive data for the user"""
        # Course progress
        total_courses = Enrollment.objects.filter(student=user).count()
        completed_courses = Enrollment.objects.filter(student=user, completed=True).count()

        # Lesson progress
        total_lessons = LessonProgress.objects.filter(student=user).count()
        completed_lessons = LessonProgress.objects.filter(student=user, completed=True).count()

        # Quiz perfomance
        quiz_attempts = QuizAttempt.objects.filter(student=user)
        total_attempts = quiz_attempts.count()
        passed_attempts = quiz_attempts.filter(passed=True).count()
        average_score = quiz_attempts.aggregate(Avg('score'))['score__avg'] or 0

        # Lesson time (estimated) assuming each lesson takes its duration minutes
        completed_lesson_durations = LessonProgress.objects.filter(
            student=user,
            completed=True,
        ).values_list('lesson__duration', flat=True)
        total_learning_time = sum(completed_lesson_durations) if completed_lesson_durations else 0

        return {
            'total_courses': total_courses,
            'completed_courses': completed_courses,
            'course_completion_rate': (completed_courses / total_courses * 100) if total_courses > 0 else 0,
            'total_lessons': total_lessons,
            'completed_lessons': completed_lessons,
            'lesson_completion_rate': (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0,
            'total_quiz_attemps': quiz_attempts,
            'passed_quiz_attempts': passed_attempts,
            'quiz_pass_rate': (passed_attempts / total_attempts * 100) if total_attempts > 0 else 0,
            'average_quiz_score': average_score,
            'total_learning_time_hours': total_learning_time / 60,
        }
    
    @staticmethod
    def get_course_anaytics(course):
        """Get analytics for a specific course"""
        enrollments = course.enrollments.all()
        total_enrollments = enrollments.count()
        completed_enrollments = enrollments.filter(completed=True).count()

        # Lesson progress
        lessons = lessons.objects.filter(module__course=course)
        total_lessons = lessons.count()
        completed_lessons = lessons.filter(
            lesson__module__course=course,
            completed=True
        )

        # Average lesson completion
        if total_lessons > 0 and total_enrollments > 0:
            avg_lesson_completion = (completed_lessons.count() / (total_lessons * total_enrollments)) * 100
        else:
            avg_lesson_completion = 0

        # Quiz analytics
        quizzes = course.modules.filter(lesson__quiz__isnull=False)
        quiz_attempts = QuizAttempt.objects.filter(quiz__lesson__module__course=course)
        total_quiz_attempts = quiz_attempts.count()
        avg_quiz_score = quiz_attempts.aggregate(Avg('score'))['score__avg'] or 0

        # Engagement metrices
        daily_enrollments = enrollments.filter(
            enrolled_at__gte=timezone.now() - timedelta(days=30)
        ).count()

        return {
            'total_enrollments': total_enrollments,
            'completed_enrollments': completed_enrollments,
            'completion_rate': (completed_enrollments / total_enrollments * 100) if total_enrollments > 0 else 0,
            'total_lessons': total_lessons,
            'avg_lesson_completion_': avg_lesson_completion,
            'total_quiz_attempt': total_quiz_attempts,
            'avg_quiz_score': avg_quiz_score,
            'enrollment_last_30_days': daily_enrollments,
            'rating': course.avg_rating,
            'total_reviews': course.total_reviews,
        }        
    
    @staticmethod
    def get_platform_statistics():
        """Get overall platform statistics"""
        total_users = User.objects.count()
        active_users = User.objects.filter(
            last_login__gte=timezone.now() - timedelta(days=30)
        ).count()
        
        total_courses = Course.objects.filter(is_published=True).count()
        total_enrollments = Enrollment.objects.count()
        total_completed = Enrollment.objects.filter(completed=True).count()

        # Content statistics
        total_lessons = Lesson.objects.count()
        total_quizes = Quiz.objects.count()

        # Engagement 
        total_discussions = DiscussionThread.objects.count()
        total_replies = DiscussionReply.objects.count()

        return {
            'total_users': total_users,
            'active_users': active_users,
            'user_engagement_rate': (active_users / total_users * 100) if total_users > 0 else 0,
            'total_courses': total_courses,
            'total_enrollments': total_enrollments,
            'enrollment_rate': (total_enrollments / total_courses * 100) if total_courses > 0 else 0,
            'completion_rate': (total_completed / total_enrollments * 100) if total_enrollments > 0 else 0,
            'total_lessons': total_lessons,
            'total_quizes': total_quizes,
            'total_discussions': total_discussions,
            'total_replies': total_replies,
        }