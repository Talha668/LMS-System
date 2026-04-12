from django.contrib import admin
from . models import Course, Enrollment, Module, Lesson, LessonProgress, Quiz, Question, Choice, QuizAttempt, UserAnswer, Certificate, DiscussionThread, DiscussionReply

# Register your models here.

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'instructor', 'price', 'is_published', 'created_at']
    list_filter = ['is_published', 'created_at', 'instructor']
    search_fields = ['title', 'description']
    list_editable = ['is_published']


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'enrolled_at', 'completed']
    list_filter = ['completed', 'enrolled_at']


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'order']
    list_filter = ['course']


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'module', 'duration', 'order']
    list_filter = ['module']   


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ['student', 'lesson', 'completed', 'completed_at']
    list_filter = ['completed', 'lesson__module__course']


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ['title', 'lesson', 'passing_score', 'is_active']
    list_filter = ['is_active', 'lesson__module__course']


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['question_text', 'quiz', 'question_type', 'points', 'order']
    list_filter = ['question_type', 'quiz']


@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ['choice_text', 'question', 'is_correct']
    list_filter = ['is_correct', 'question__quiz']

       
@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ['student', 'quiz', 'score', 'passed', 'started_at']
    list_filter = ['passed', 'quiz']


@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ['attempt', 'question', 'is_correct']
    list_filter = ['is_correct']


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ['certificate_id', 'student', 'course', 'issued_at']
    list_filter = ['issued_at', 'course']
    search_fields = ['certificate_id', 'student__username', 'course__title']


@admin.register(DiscussionThread)
class DiscussionThreadAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'author', 'created_at', 'is_pinned', 'is_locked', 'reply_count']
    list_filter = ['is_pinned', 'is_locked', 'created_at', 'course']
    search_fields = ['title', 'content', 'author__username']
    list_editable = ['is_pinned', 'is_locked']


@admin.register(DiscussionReply)
class DiscussionReplyAdmib(admin.ModelAdmin):
    list_display = ['thread', 'author', 'created_at', 'is_answer']
    list_filter = ['is_answer', 'created_at', 'thread__course']
    search_fields = ['content', 'author__username', 'thread__title']