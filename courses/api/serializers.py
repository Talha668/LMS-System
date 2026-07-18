from rest_framework import serializers
from django.contrib.auth.models import User
from courses.models import Course, Lesson, Module, Enrollment, Quiz, Question
from users.models import Profile








class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        extra_kwargs = {'password': {'write_only': True}}


class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = ['user', 'bio', 'profile_picture', 'user_type', 'xp', 'level']


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ['id', 'title', 'context', 'video_url', 'duration', 'order', 'prerequisites']


class ModuleSerialzer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = Module
        fields = ['id', 'title', 'description', 'order', 'lessons']


class CourseSerializer(serializers.ModelSerializer):
    modules = ModuleSerialzer(many=True, read_only=True)
    instructor = UserSerializer(read_only=True)
    enrollment_count = serializers.IntegerField(source='enrollment.count', read_only=True)

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'description', 'instructor', 'price',
            'thumbnail', 'category', 'level', 'average_rating',
            'total_reviews', 'modules', 'enrollment_count',
            'created_at', 'is_published'
        ]        


class QuizSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz
        fields = ['id', 'question_text', 'question_type', 'points', 'order']


class EnrollmentSerializer(serializers.ModelSerializer):
    course = CourseSerializer(read_only=True)
    progress_percentage = serializers.SerializerMethodField()

    class Meta:
        model = Enrollment
        fields = ['id', 'course', 'enrollment_at', 'completed', 'progress_percentage']

    def get_progress_percentage(self, obj):
        return obj.progress_percentage()    