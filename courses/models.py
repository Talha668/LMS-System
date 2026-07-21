from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid










class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    instructor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses_taught')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    thumbnail = models.ImageField(upload_to='course_thumbnails/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=False)

    # New fields
    category = models.ForeignKey('Category', on_delete=models.CASCADE, blank=True, null=True, related_name='courses')
    level = models.CharField(max_length=20, choices=[
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced')
    ], default='beginner')
    average_rating = models.FloatField(default=0.0)
    total_reviews = models.IntegerField(default=0)

    def __str__(self):
        return self.title
    
    def update_rating(self):
        """Calculate and update average rating"""
        from .models import Rating
        ratings = Rating.objects.filter(course=self)
        if ratings.exists():
            self.average_rating = ratings.aggregate(models.Avg('rating'))['rating__avg']
            self.total_reviews = ratings.count()
        else:
            self.average_rating = 0
            self.total_reviews = 0
        self.save()

    def get_next_lesson(self, current_lesson):
        """Get next lesson in the course"""
        try:
            return Lesson.objects.filter(
                module__course=self,
                order__gt=current_lesson.order
            ).order_by('order').first()
        except:
            return None
        
    def get_prvious_lesson(self, current_lesson):
        """Get previous lesson in the course"""
        try:
            return Lesson.objects.filter(
                module__course=self,
                order__lt=current_lesson.order
            ).order_by('order').first()
        except:
            return None

    
class Enrollment(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ['student', 'course']
        
    def completed_lessons_count(self):
        """Return number of completed lessons in this course"""
        return LessonProgress.objects.filter(
            student=self.student,
            lesson__module__course=self.course,
            completed=True
        ).count()
    
    def total_lessons_count(self):
        return Lesson.objects.filter(module__course=self.course).count()
    
    def progress_percentage(self):
        total = self.total_lessons_count()
        if total == 0:
            return 0
        completed = self.completed_lessons_count()
        return int((completed / total) * 100)
    
    def is_course_completed(self):
        return self.completed_lessons_count() == self.total_lessons_count()
    
    def __str__(self):
        return f"{self.student.username} - {self.course.title}" 
    
    def mark_completed(self):
        """Mark Enrollment as completed and generate certificate"""
        if not self.completed:
            self.completed = True
            self.save()

            # Auto generate certificate
            Certificate.objects.get_or_create(
                student=self.student,
                Course=self.course
            )
            return True
        return  False


class Module(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.course.title} - {self.title}"
    
    def lesson_count(self):
        return self.lessons.count()
        

class Lesson(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    content = models.TextField()
    video_url = models.URLField(blank=True, null=True)
    duration = models.PositiveIntegerField(help_text='Duration in minutes')
    order = models.PositiveIntegerField(default=0)
    video_file = models.FileField(
        upload_to='lesson_videos/',
        null=True,
        blank=True,
        help_text="Upload video file for the lesson"
    )
    video_duration = models.PositiveBigIntegerField(
        null=True,
        blank=True,
        help_text="Video duration in seconds"
    )
    video_thumbnail = models.ImageField(
        upload_to='video_thumbnail/',
        null=True,
        blank=True
    )
    allow_download = models.BooleanField(
        default=False,
        help_text="Allow students to download the video"
    )

    prerequisites = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
        related_name='dependent_lesson',
        help_text="Lessons that must be completed before this one"
    )

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title    

    def get_prerequisites_completed(self, user):
        """Check if all prerequisites are completed by the user"""
        if not self.prerequisites.exists():
            return True
        return all(
            LessonProgress.objects.filter(
                student=user,
                lesson=prereq,
                completed=True
            ).exists()
            for prereq in self.prerequisites.all()
        )
    
    def get_unlocked_status(self, user):
        """Get unlock status for this lesson"""
        if not user.is_authenticated:
            return False
        return self.get_prerequisites_completed(user)
    

class LessonProgress(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lesson_progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='progress')
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['student', 'lesson']

    def __str__(self):
        return f"{self.student.username} - {self.lesson.title} - {'completed' if self.completed else 'in progress'}"


class Quiz(models.Model):   
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE, related_name='quiz')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    passing_score = models.IntegerField(default=70)
    time_limit = models.IntegerField(default=30, help_text="Time limit in minutes")
    max_attempts = models.IntegerField(default=3, help_text="Maximum number of attempts")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"quiz: {self.title} - {self.lesson.title}"


class Question(models.Model):
    QUESTION_TYPES = [
        ('multiple_choice', 'Multiple Choice'),
        ('true_false', 'True/False'),
        ('short_answers', 'Short Answer'),
    ]           

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='multiple_choice')
    points = models.IntegerField(default=1)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Q{self.order}: {self.question_text[:50]}..."


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    choice_text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.choice_text} {('Correct') if self.is_correct else ''}"


class QuizAttempt(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_attempts')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    score = models.FloatField(null=True, blank=True)
    passed = models.BooleanField(default=False)
    current_question = models.IntegerField(default=0)

    def time_spent(self):
        if self.completed_at and self.started_at:
            return (self.completed_at - self.started_at).total_seconds() // 60
        return 0
    
    def __str__(self):
        return f"{self.student.username} - {self.quiz.title} - {self.score}%"
    

class UserAnswer(models.Model):
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='user_answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_choice = models.ForeignKey(Choice, on_delete=models.CASCADE, null=True, blank=True)
    text_answer = models.TextField(blank=True)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"Answer for {self.question}"    
    

class Certificate(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='certificates')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='certificates')
    issued_at = models.DateTimeField(auto_now_add=True)
    certificate_id = models.CharField(max_length=100, unique=True)
    download_url = models.URLField(blank=True, null=True)

    class Meta:
        unique_together = ['student', 'course']

    def __str__(self):
        return f"Certificate {self.certificate_id} - {self.student.username} - {self.course.title}"

    def generate_certificate_id(self):
        return f"CERT-{uuid.uuid4().hex[:12].upper()}"

    def save(self, *args, **kwargs):
        if not self.certificate_id:
            self.certificate_id = self.generate_certificate_id()
        super().save(*args, **kwargs)


class DiscussionThread(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='discussion_threads')
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='discussion_threads')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_pinned = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)

    class Meta:
        ordering = ['-is_pinned', '-created_at']

    def __str__(self):
        return f"{self.title} - {self.course.title}"

    def reply_count(self):
        return self.replies.count()


class DiscussionReply(models.Model):
    thread = models.ForeignKey(DiscussionThread, on_delete=models.CASCADE, related_name='replies')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='discussion_replies')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_answer = models.BooleanField(default=False)  # Mark as correct answer

    class Meta:
        ordering = ['created_at']
        verbose_name_plural = "Discussion_replies"

    def __str__(self):
        return f"Reply by {self.author.username} on {self.thread.title}"  


class Rating(models.Model):
    """Course rating and reviews"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_ratings')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    review = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        uniques_together = ['course', 'user']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.course.title} - {self.rating}★"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.course.update_rating()    


class Category(models.Model):
    """Course categories for better organization"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Font awesome icon class")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')
    order = models.PositiveBigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name
    
    def get_subcategories(self):
        return self.subcategories.all()
    
    def course_count(self):
        return self.courses.count()
        
        
class LearningPath(models.Model):
    """A structured learning journey with multiple courses"""
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField()
    image = models.ImageField(upload_to='mearning_fields/', null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    level = models.CharField(max_length=20, choices=[
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advances', 'Advanced'),
    ], defailt='beginner')
    extimated_duration = models.PositiveBigIntegerField(help_text='Estimated duartion in hours')
    is_publised = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

        def __str__(self):
            return self.title
        
        def total_courses(self):
            return self.path_courses.count()
        
        def total_enrollment(self):
            return LearningPathEnrollment.objects.filter(path=self).count()
        
        def completion_rate(self):
            enrollments = LearningPathEnrollment.objects.filter(path=self)
            if not enrollments.exists():
                return 0
            completed = enrollments.filter(completed=True).count()
            return int((completed / enrollments.count()) * 100)
        

class LearningPathCourse(models.Model):
    """Link courses to learning path in order"""
    path = models.ForeignKey(LearningPath, on_delete=models.CASCADE, related_name='path_courses')
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    order = models.PositiveBigIntegerField(default=0)
    is_required = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']
        uniques_together = ['path', 'course']

    def __str__(self):
        return f"{self.path.title} - {self.course.title}"


class LearningPathEnrollment(models.Model):
    """Track user enrollment in learning path"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='path_enrollments')
    path = models.ForeignKey(LearningPath, on_delete=models.CASCADE, related_name='enrollments')
    enrollment_at = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    progress = models.FloatField(default=0.0)   # 0-100

    class Meta:
        uniques_together = ['user', 'path']

    def __str__(self):
        return f"{self.user.username} - {self.path.title}"

    def calculate_progress(self):
        """Calculate progress based on completed courses in path"""
        total_courses = self.path.path_courses.count()
        if total_courses == 0:
            return 0
        
        completed_courses = self.user.enrollments.filter(
            course__in=self.path.path_courses.values_list('course', flat=True),
            completed=True
        ).count()

        progress = (completed_courses / total_courses) * 100
        self.progress = progress
        self.save()

        if progress == 100 and not self.completed:
            self.completed = True
            self.completed_at = timezone.now()
            self.save()

        return progress  


class Bookmark(models.Model):
    """User bookmarks for lessons"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmarks')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='bookmarks')
    note = models.TextField(blank=True, help_text="Optional mote for the bookmarks")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'lesson']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.lesson.title}"    
    

class Payment(models.Model):
    """Payment records for course purchases"""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_id = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.course.title} - {self.status}"    


class Achievement(models.Model):
    """User achievements and badges"""
    ACHIEVEMENT_TYPES = [
        ('course', 'Course Achievement'),
        ('quiz', 'Quiz Achievement'),
        ('streak', 'Streak Achievement'),
        ('level_up', 'Level Up'),
        ('special', 'Special Achievement'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    name = models.CharField(max_length=100)
    description = models.TextField()
    type = models.CharField(max_length=20, choices=ACHIEVEMENT_TYPES)
    points = models.PositiveBigIntegerField(default=0)
    icon = models.CharField(max_length=50, blank=True, help_text='Font Awesome icon class')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'name']

    def __str__(self):
        return f"{self.name.username} - {self.name}"    
    

class VideoProgress(models.Model):
    """Track video viewing progress"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='video_progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='video_progress')
    current_time = models.PositiveBigIntegerField(default=0, help_text="Current position in seconds")
    total_watched = models.PositiveBigIntegerField(default=0, help_text="Total time watched in second")
    completed = models.BooleanField(default=False)
    last_watched = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'lesson']

    def __str__(self):
        return f"{self.user.username} - {self.lesson.title} - {self.current_time}s"

    def update_progress(self, current_time):
        self.current_time = current_time

        # If vudeo duration is set and user has matched enough
        if self.lesson.video_duration:
            watched_percentage = (current_time / self.lesson.video_duration) * 100
            if watched_percentage >= 80:     # Mark as completed if 80% watched
                self.completed = True
                # Mark lesson as completed
                LessonProgress.objects.get_or_create(
                    student=self.user,
                    lesson=self.lesson,
                    defaults={f'completed': True, 'completed_at': timezone.now()}
                )

        self.save()        