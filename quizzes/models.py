from django.db import models
from courses.models import Lesson
from django.contrib.auth.models import User







class Quiz(models.Model):
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE, related_name='quiz')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    time_limit = models.PositiveBigIntegerField(help_text='Time limit in minutes', default=30)
    passing_score = models.PositiveBigIntegerField(default=70)

class Questions(models.Model):
    QUESTION_TYPE = (
        ('multiple-choice', 'Multiple Choice'),
        ('true_false', 'True/False'),
        ('short_answer', 'Short Answer'),
    )

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE)
    text = models.TextField()
    order = models.PositiveBigIntegerField(default=0)

    class Meta:
        ordering = ['order']

class Choice(models.Model):
    question = models.ForeignKey(Questions, on_delete=models.CASCADE, related_name='choices')
    text = models.CharField(max_length=200)
    is_correct = models.BooleanField(default=False)

class QuizAttempt(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    score = models.FloatField()
    completed_at = models.DateTimeField(auto_created=True)     