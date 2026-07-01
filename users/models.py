from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone






class Profile(models.Model):
    USER_TYPES = (
        ('student', 'Student'),
        ('instructor', 'Instructor'),
        ('admin', 'Adminstrator'),
    )


    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='student')
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)

    # New fields
    website = models.URLField(blank=True, null=True)
    twitter = models.URLField(blank=True, null=True)
    linkedln = models.URLField(blank=True, null=True)
    github = models.URLField(blank=True, null=True)
    expertise = models.CharField(max_length=255, blank=True, name=True)
    is_email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=255, blank=True, null=True)
    last_activity = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} Profile"
    
    def is_intructor(self):
        return self.user_type == 'instructor' 
    
    def is_student(self):
        return self.user_type == 'student'
    
    def get_courses_teaching(self):
        """Get course where user is instructor"""
        if self.is_instructor():
            return self.user.courses_taught.all()
        return []
    
    def get_enrolled_courses(self):
        """Get courses user is enrolled in"""
        return self.user.enrollments.all()
    
    def get_completed_courses(self):
        """Get courses user has competed"""
        return self.user.enrollments.filter(completed=True)
    
    def get_total_completed_lessons(self):
        """Get total number of completed lessons"""
        from courses.models import LessonProgress
        return LessonProgress.objects.filter(
            student=self.user,
            completed=True
        ).count()
    
    def get_certificate(self):
        """get all certificates earned"""
        from courses.models import Certificate
        return Certificate.objects.filter(student=self.user)