from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Course, Enrollment, LessonProgress, QuizAttempt, Achievement
from users.models import Profile








class GamificationService:
    """Service for managing gamifucation features"""
    @staticmethod
    def award_xp(user, amount, reason):
        """Award XP points to a user"""
        profile = user.profile
        profile.xp = getattr(profile, 'xp', 0) + amount
        profile.save()

        # Check for level up
        GamificationService.check_level_up(user)

        # Check for achivements
        GamificationService.check_achievements(user)

    
    @staticmethod
    def check_level_up(user):
        """Chceck if user should level up"""
        profile = user.profile
        xp = getattr(profile, 'xp', 0)
        level = getattr(profile, 'xp', 1)

        # XP required for next level (increase with level)
        xp_needed =  level * 100

        while xp>=xp_needed:
            level += 1
            xp_needed = level * 100

            # Create level up achievement
            Achievement.objects.create(
                user=user,
                name=f'Level {level} Achieved!',
                description=f'Reached level {level}',
                type='level_up',
                points=50
            )

        profile.level = level
        profile.save()


    @staticmethod
    def check_achiviements(user):
        """Check and award achievements"""
        # Course completion achievements
        completed_course = Enrollment.objects.filter(
            student=user,
            completed=True
        ).count()

        if completed_course == 1:
            GamificationService.create_achievement(
                user, 'First Course Completed!',
                'Completed your first course', 'course'
            )
        elif completed_course == 5:
            GamificationService.create_achievement(
                user, 'Course Enthusiast!',
                'Completed 5 courses', 'course'
            )    
        elif completed_course == 10:
            GamificationService.create_achievement(
                user, 'Course Master!',
                'Completed 10 courses', 'course'
            )    

        # Quiz avhievements
        passed_quizzes = QuizAttempt.objects.filter(
            student=user,
            passed=True
        ).count()

        if passed_quizzes == 1:
            GamificationService.create_achievement(
                user, 'Quiz Champion!',
                'Passed your first quiz', 'quiz'
            )    
        elif passed_quizzes == 10:
            GamificationService.create_achievement(
                user, 'Quiz Expert!',
                'Passed 10 quizzes', 'quiz'
            )    

        # Streak achievements (daily learning)
        # This would require tracking daily activity
        # simplifies version
        recent_lessons = LessonProgress.objects.filter(
            student=user,
            completed_at__gte=timezone.now() - timezone.timedelta(days=7)
        ).count()

        if recent_lessons >= 7:
            GamificationService.create_achievement(
                user, 't-Streak!',
                'Learned for 7 consecutive days', 'streak'
            )    


    @staticmethod
    def create_achievement(user, name, description, type):
        """Create an achievement if it doesn't exist"""
        achievement, created = Achievement.objects.get_or_create(
            user=user,
            name=name,
            defaults={
                'description': description,
                'type': type,
                'points': 50
            }
        )            
        return achievement
    

    @staticmethod
    def get_leaderboard(limit=10):
        """Get top users by XP"""
        profiles = Profile.objects.filter(
            xp__gt=0
        ).order_by('-xp')[:limit]

        leaderboard = []
        for profile in profiles:
            leaderboard.append({
                'user': profile.user,
                'level': profile.level,
                'xp': profile.xp,
                'achievements': Achievement.objects.filter(user=profile.user).count()
            })

        return leaderboard    