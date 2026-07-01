from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.contrib.auth.models import User
from .models import Course, Enrollment, DiscussionReply, DiscussionThread











class EmailService:
    """Service class for sending various email notifications"""
    @staticmethod
    def send_welcome_email(user):
        """Send welcome email to new user"""
        subject = f"Welcome to the LMS Learning Platform, {user.get_full_name()}!"
        context = {
            'user': user,
            'platform_name': 'LMS Learning Platform'
        }       
        EmailService.send_html_email(
            subject=subject,
            template_name='emails/welcome.html',
            context=context,
            recipient_list=[user.email]
        )

    @staticmethod
    def send_course_enrollment_email(user, course):
        """send enrollment confirmation mail"""
        subject = f"Enrollment in {course.title}"
        context = {
            'user': user,
            'course': course,
            'platform_name': 'LMS Learning Platform'
        }    
        EmailService.send_html_email(
            subject=subject,
            template_name='emails/enrollment.html',
            context=context,
            recipient_list=[user.email]
        )

    @staticmethod
    def send_course_completion_email(user, course):
        """Send course completion notification"""
        subject = f"🎉 Congratulations! Completed {course.title}"
        context = {
            'user': user,
            'course': course,
            'paltform_name': 'LMS Learning Platform'
        }    
        EmailService.send_html_email(
            subject=subject,
            template_name='emails/course_completed.html',
            context=context,
            recipient_list=[user.email]
        )

    @staticmethod
    def send_quiz_result_email(user, quiz, attempt):
        """Send quiz results email"""
        subject = f"Quiz Results: {quiz.title}"
        context = {
            'user': user,
            'quiz': quiz,
            'attempt': attempt,
            'score': attempt.score,
            'passed': attempt.passed,
            'platform_name': 'LMS Learning Platform'
        }    
        EmailService.send_html_email(
            subject=subject,
            template_name='emails/quiz_results.html',
            context=context,
            recipient_list=[user.email]
        )

    @staticmethod
    def send_discussion_reply_email(user, thread, reply):
        """Send notification for new discussion reply"""
        subject = f"New Reply in Discussion: {thread.title}"
        context = {
            'user': user,
            'thread': thread,
            'reply': reply,
            'course': thread.course,
            'platform_name': 'LMS Learning Platform'
        }    
        EmailService.send_html_email(
            subject=subject,
            template_name='emails/discussion_reply.html',
            context=context,
            recipient_list=[user.email]
        )

    @staticmethod
    def send_learning_path_completion_email(user, path):
        """Send learning path completion notification"""
        subject = f"🎉 Completed Learning Path: {path.title}"
        context = {
            'user': user,
            'path': path,
            'platform_name': 'LMS Learning Platform'
        }    
        EmailService.send_html_email(
            subject=subject,
            template_name='emails/path_completed.html',
            context=context,
            recipient_email=[user.email]
        )

    @staticmethod
    def send_html_email(subject, template_name, context, recipient_list):
        """Send HTML email with plain text fallback"""
        try:
            html_context = render_to_string(template_name, context)
            text_context = strip_tags(html_context)

            email = EmailMultiAlternatives(
                subject=subject,
                body=text_context,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=recipient_list
            )   
            email.attach_alternative(html_context, "text/html")
            email.send(fail_silently=True)
        except Exception as e:
            # Log error but don't fail
            print(f"Email sending failed: {str(e)}")

