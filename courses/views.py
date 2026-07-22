from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import models
from .models import (
    Course, Enrollment, Lesson, QuizAttempt, Quiz, UserAnswer, Certificate,
    DiscussionReply, DiscussionThread, LessonProgress, Rating, Category, LearningPath,
    LearningPathEnrollment, Bookmark, User
)
from .forms import UserAnswerForm, DiscussionThreadForm, DiscussionReplyForm, RatingForm
from django.utils import timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch 
from reportlab.lib import colors
from django.http import HttpResponse, JsonResponse
from django.db.models import Avg, Count, Q
from django.core.mail import send_mail
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .analytics import AnalyticsService
from .notifications import EmailService
from .payment import LemonSqueezyPaymentService
from datetime import timedelta










def course_list(request):
    """Course list with search and filter"""
    courses = Course.objects.filter(is_published=True)

    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        courses = courses.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(category__name__icontains=search_query) |
            Q(instructor__username__icontains=search_query) |
            Q(isntructor__firstname__icontains=search_query) |
            Q(instructor__lastname__icontains=search_query)
        )

        # Filter by category
        category_slug = request.GET.get('category', '')
        if category_slug:
            courses = courses.filter(category__slug=category_slug)

        # Filter by level
        level = request.GET.get('level', '')
        if level:
            courses = courses.filter(level=level)

        # Filter by price
        price_type = request.GET.get('price', '')
        if price_type == 'free':
            courses = courses.filter(price=0)
        if price_type == 'paid':
            courses = courses.filter(price__gt=0)

        # Filter by rating
        min_rating = request.GET.get('rating', '')
        if min_rating:
            try:
                min_rating = float(min_rating)
                courses = courses.filter(average_rating__gt=min_rating)
            except ValueError:
                pass

        # Sort options
        sort = request.GET.get('sort', 'newest')
        if sort == 'newest':
            courses = courses.order_by('-created_at')
        elif sort == 'popular':
            courses = courses.filter(enrollment_count=Count('enrollments')).order_by('-enrollment_count')
        elif sort == 'rating' :
            courses = courses.order_by('-average_rating')
        elif sort == 'price_low':
            courses = courses.order_by('price')
        elif sort ==  'price_hign':
            courses = courses.order_by('-price')
        elif sort == 'title':
            courses = courses.order_by('title')

        # Get categories for filter
        categories = Category.objects.all()

        # Get lerning path for recommedations
        learning_paths = LearningPath.objects.filter(is_published=True)[:3]

        # pagination
        paginator = Paginator(courses, 12)     # 12 courses per page
        page = request.GET.get('page')
        try:
            courses = paginator.page(page)
        except PageNotAnInteger:
            courses = paginator.page(1)
        except EmptyPage:
            courses = paginator.page(paginator.num_pages)

        context = {
            'courses': courses,
            'search_query': search_query,
            'categpory_slug': category_slug,
            'level': level,
            'price_type': price_type,
            'min_rating': min_rating,
            'sort': sort,
            'categories': categories,
            'learning_paths': learning_paths
        }  

        return render(request, 'courses/courses_list.html', context) 


def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    is_enrolled = False
    is_instructor = False

    if request.user.is_authenticated:
        is_enrolled = Enrollment.objects.filter(student=request.user, course=course).exists()
        is_instructor = request.user == course.instructor

    # get rating
    ratings = course.ratings.all()

    # Rating form
    rating_form = RatingForm()
    user_rating = None
    if request.user.is_authenticated:
        user_rating = Rating.objects.filter(course=course, user=request.user).first()

    context = {
        'course': course,
        'is_enrolled': is_enrolled,
        'is_instructor': is_instructor,
        'ratings': ratings,
        'rating_form': rating_form,
        'user_rating': user_rating,
    }    
    return render(request,'courses/course_detail.html', context)


@login_required
def enroll_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    # To check if the user is already enrolled
    if Enrollment.objects.filter(student=request.user, course=course,).exists():
        messages.warning(request, 'You are already enrolled in this course')
    else:
        Enrollment.objects.create(student=request.user, course=course)
        messages.success(request, f'Successfully enrolled in {course.title}!')

        # Send enrollment email
        try:
            send_mail(
                f'Enrollment in {course.title}',
                f'Dear {request.user.get_full_name()},\n\n'
                f'you have successfully enrolled in "{course.title}".\n\n'
                f'Start learning now!\n\n'
                f'Best ragards,\n'
                f'The LMS Team',
                settings.DEFAULT_FROM_EMAIL,
                [request.user.email],
                fail_silently=True,
            )
        except:
            pass    

    return redirect('course_detail', course_id=course_id)


@login_required
def my_courses(request):
    enrollments = Enrollment.objects.filter(student=request.user)
    return render(request, 'courses/my_courses.html', {'enrollments': enrollments})


@login_required
def course_dashboard(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    enrollment = get_object_or_404(Enrollment, student=request.user, course=course)

    # Update course completion status
    if enrollment.progress_percentage() == 100 and not enrollment.completed:
        enrollment.mark_completed()  # This now generate certificate too
        messages.success(request, f"Congratulation! You've completed {course.title}! 🎉")

        # Send completion email
        try:
            send_mail(
                f'Course completed: {course.title}',
                f'Dear {request.user.get_full_name()},\n\n'
                f'Congratulations on completing "{course.title}"!\n\n'
                f'Your certificate is now available on your profile.\n\n'
                f'Keep learning!\n\n'
                f'Best ragards,\n'
                f'The LMS Team',
                settings.DEFAULT_FROM_EMAIL,
                [request.user.email],
                fail_silently=True,
            )
        except:
            pass

    # To check if the certificate even exists
    has_certificate = Certificate.objects.filter(student=request.user, course=course).exists()    

    # get next lesson
    next_lesson = None
    completed_lessons = LessonProgress.objects.filter(
        student=request.user,
        lesson__module__course=course,
        completed=True
    ).values_list('lesson_id', flat=True)

    all_lessons = Lesson.objects.filter(module__course=course).order_by('order')
    for lesson in all_lessons:
        if lesson.id not in completed_lessons:
            if lesson.get_prerequisites_completed(request.user):
                next_lesson = lesson
                break

    context = {
        'course': course,
        'enrollment': enrollment,
        'has_certificate': has_certificate,
        'next_lesson': next_lesson,
    }        
    return render(request, 'courses/course_dashboard.html', context)       


@login_required
def lesson_detail(request, course_id, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id, module__course_id=course_id)
    course = lesson.module.course

    # Check if the user is enrolled
    if not Enrollment.objects.filter(student=request.user, course=course,).exists():
        messages.error(request, 'You need to enroll in this course first')
        return redirect('course_detail', course_id=course_id)
    
    # Check prerequisites
    if not lesson.get_prerequisites_completed(request.user):
        messages.warning(request, 'You need to complete the prerequisites for this lesson first.')
        return redirect('course_dashboad', course_id=course_id)
    
    # Get or create lesson progress
    lesson_progress, created = LessonProgress.objects.get_or_create(student=request.user, lesson=lesson)

    # Get next or previous lessons
    next_lesson = course.get_next_lesson(lesson)
    previous_lesson = course.get_prvious_lesson(lesson)

    context = {
        'lesson': lesson,
        'course': course,
        'lesson_progress': lesson_progress,
        'next_lesson': next_lesson,
        'previous_lesson': previous_lesson,
    }
    return render(request, 'courses/lesson_detail.html', context)


@login_required
def mark_lesson_completed(request, course_id, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id, module__course_id=course_id)

    lesson_progress, created = LessonProgress.objects.get_or_create(
        student=request.user,
        lesson=lesson
    )

    if not lesson_progress.completed:
        lesson_progress.completed = True
        lesson_progress.completed_at = timezone.now()
        lesson_progress.save()
        messages.success(request, "Lesson marked as complete")

    return redirect('lesson_detail', course_id=course_id, lesson_id=lesson_id)


@login_required
def start_quiz(request, course_id, lesson_id):
    print("=== START QUIZ DEBUG===")
    print(f"User: {request.user}")
    print(f"Course ID: {course_id}, Lesson ID: {lesson_id}")

    try:
        lesson = get_object_or_404(Lesson, id=lesson_id, module__course_id=course_id)
        print(f"found lesson: {lesson.title}")

        quiz = get_object_or_404(Quiz, lesson=lesson, is_active=True)
        print(f"found quiz: {quiz.title}")

        # Check if the user is enrolled
        is_enrolled = Enrollment.objects.filter(student=request.user, course=lesson.module.course).exists()
        print(f"User enrolled: {is_enrolled}")

        if not is_enrolled:
            messages.error(request, 'You need to enroll in this course first.')
            return redirect('course_detail', course_id=course_id)
        
        #Check the attempts limit
        attempts_count = QuizAttempt.objects.filter(student=request.user, quiz=quiz).count()
        print(f"Current attempts: {attempts_count}, Max attempts: {quiz.max_attempts}")

        if attempts_count >= quiz.max_attempts:
            messages.error(request, f'You have reached the maximum number of attempts ({quiz.max_attempts}) for this quiz')
            return redirect('lesson_detail', course_id=course_id, lesson_id=lesson_id)
        
        # Create new attempt
        attempt = QuizAttempt.objects.create(
            student=request.user,
            quiz=quiz,
            current_question=0,
        )
        print(f"Created attempt: {attempt.id}")

        # Debug the redirect that has stopped us from starting the quiz
        redirect_url = f"/course/{course_id}/lesson/{lesson_id}/quiz/{attempt.id}/"
        print(f"Redirecting to: {redirect_url}")

        return redirect('take_quiz', course_id=course_id, lesson_id=lesson_id, attempt_id=attempt.id)
    
    except Exception as e:
        print(f"ERROR in start_quiz: {str(e)}")
        import traceback
        print(traceback.format_exc())
        messages.error(request, f"Error starting quiz: {str(e)}")
        return redirect('lesson_detail', course_id=course_id, lesson_id=lesson_id)


def process_quiz_answer(attempt, question, cleaned_data):
    """
    Save or updates the user answer and determines if it is correct or not
    """
    # Get or create the answer record
    user_answer, created = UserAnswer.objects.get_or_create(
        attempt=attempt,
        question=question,
        defaults=cleaned_data
    )

    # If it already exists update the fields
    if not created:
        user_answer.selected_choice = cleaned_data.get('selected_choice')
        user_answer.text_answer = cleaned_data.get('text_answer')
        user_answer.save()

    # Determine correctness based on question type
    is_correct = False

    if question.question_type in ['multiple_choice', 'true_false']:
        if user_answer.selected_choice:
            is_correct = user_answer.selected_choice.is_correct
    
    elif question.question_type == 'short_answer':
        correct_answer = question.choices.filter(is_correct=True).first()
        if correct_answer:
            is_correct = user_answer.text_answer.lower().strip() == correct_answer.choice_text.lower().strip()

    user_answer.is_correct = is_correct
    user_answer.save()  


def get_quiz_context(attempt, quiz, current_question, course_id, lesson_id):
    """Helper function to prepare quiz context"""
    form = UserAnswerForm(question=current_question)
    questions_count = quiz.questions.count()

    return {
        'attempt': attempt,
        'quiz': quiz,
        'current_question': current_question,
        'form': form,
        'progress': ((attempt.current_question) / questions_count) * 100,
        'course_id': course_id,
        'lesson_id': lesson_id,
    }        


def handle_quiz_submission(request, attempt, questions, course_id, lesson_id):
    """Helper function to handle quiz form submission"""
    question = questions[attempt.current_question]
    form = UserAnswerForm(request.POST, question=question)

    if form.is_valid():
        # Use helper function to process logic
        process_quiz_answer(attempt, question, form.cleaned_data)

        # Move to next question or finish quiz
        attempt.current_question += 1
        if attempt.current_question >= questions.count():
            return redirect('finish_quiz', course_id=course_id, lesson_id=lesson_id, attempt_id=attempt.id)
        else:
            attempt.save()

    return None       


@login_required
def take_quiz(request, course_id, lesson_id, attempt_id):
    try:
        attempt = get_object_or_404(QuizAttempt, id=attempt_id, student=request.user)
        quiz = attempt.quiz
        questions = quiz.questions.all()
        print(f"DEBUG: Quiz {quiz.title} has {questions.count()} questions")

        if not questions.exists():
            messages.error(request, 'This quiz has no questions yet.')
            return redirect('lesson_detail', course_id=course_id, lesson_id=lesson_id)
        
        # Handle form submission
        if request.method == 'POST':
            result = handle_quiz_submission(request, attempt, questions, course_id, lesson_id)
            if result:
                return result

        # Prepare data for rendering
        if attempt.current_question < questions.count():
            current_question = questions[attempt.current_question]
            context = get_quiz_context(attempt, quiz, current_question, course_id, lesson_id)         
            return render(request, 'courses/take_quiz.html', context)
        else:
            # If user get here without finish redirect to finish
            return redirect('finish_quiz', course_id=course_id, lesson_id=lesson_id, attempt_id=attempt.id)

    except Exception as e:
        print(f"ERROR in take_quiz: {e}")
        import traceback
        print(traceback.format_exc())
        messages.error(request, f"Error loading quiz: {e}")
        return redirect('lesson_detail', course_id=course_id, lesson_id=lesson_id)


@login_required
def finish_quiz(request, course_id, lesson_id, attempt_id):
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, student=request.user)
    quiz = attempt.quiz

    if not attempt.completed_at:
        total_questions = quiz.questions.count()
        correct_answers = UserAnswer.objects.filter(attempt=attempt, is_correct=True).count()

        attempt.score = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
        attempt.passed = attempt.score >= quiz.passing_score
        attempt.completed_at = timezone.now()
        attempt.save()

        # Mark lesson as completed if quiz passed
        if attempt.passed:
            lesson_progress, created = LessonProgress.objects.get_or_create(
                student=request.user,
                lesson=quiz.lesson
            )
            if not lesson_progress.completed:
                lesson_progress.completed = True
                lesson_progress.completed_at = timezone.now()
                lesson_progress.save()
                messages.success(request, "Quiz passes! Lesson marked as completed.")

    return render(request, 'courses/quiz_results.html', {
        'attempt': attempt,
        'quiz': quiz,
        'course_id': course_id,
        'lesson_id': lesson_id,
    })            


@login_required
def quiz_results(request, course_id, lesson_id, attempt_id):
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, student=request.user)
    user_answers = attempt.user_answers.select_related('question').all()

    return render(request, 'courses/quiz_detail_results.html', {
        'attempt': attempt,
        'quiz': attempt.quiz,
        'user_answers': user_answers,
        'course_id': course_id,
        'lesson_id': lesson_id,
    })


@login_required
def generate_certificate(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    # Check if user has completed the course
    enrollment = get_object_or_404(Enrollment, student=request.user, course=course)
    if not enrollment.completed:
        messages.error(request, 'You need to complete the course first')
        return redirect('course_dashboard', course_id=course_id)
    
    # Check if certificate already exists
    certificate, created = Certificate.objects.get_or_create(
        student=request.user,
        course=course
    )

    # Generate PDF
    response = HttpResponse(content_type='application/pdf')
    filename = f"certificate_{course.title.replace(' ', '_')}_{request.user.username}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    # Create PDf
    doc = SimpleDocTemplate(response, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        textColor=colors.darkblue,
        alignment=1  # Center alligned
    )

    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=14,
        spaceAfter=12,
        alignment=1
    )

    # Certificate content
    story.append(Spacer(1, 2*inch))

    # Title
    story.append(Paragraph("CERFIFICATE OF COMPLETION", title_style))
    story.append(Spacer(1, 0.5*inch))

    # this certifies that
    story.append(Paragraph("This certifies that", normal_style))
    story.append(Spacer(1, 0.2*inch))

    # Student name
    course_style = ParagraphStyle(
        'CourseStyle',
        parent=styles['Heading2'],
        fontSize=20,
        spaceAfter=20,
        textColor=colors.darkgreen,
        alignment=1
    )
    story.append(Paragraph(f'"{course.title}"', course_style))
    story.append(Spacer(1, 0.5*inch))
    
    # Date and details
    completion_date = enrollment.enrolled_at.strftime("%B %d, %Y")
    story.append(Paragraph(f"Completed on: {completion_date}", normal_style))
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph(f"Certificate ID: {certificate.certificate_id}", normal_style))
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph(f"Instructor: {course.instructor.get_full_name() or course.instructor.username}", normal_style))
    
    # Footer
    story.append(Spacer(1, 1*inch))
    story.append(Paragraph("LMS Learning Platform", normal_style))
    
    # Build PDF
    doc.build(story)
    
    return response

@login_required
def my_certificates(request):
    certificates = Certificate.objects.filter(student=request.user)
    return render(request, 'courses/my_certificates.html', {
        'certificates': certificates
    })


@login_required
def course_discussions(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    # Check if the user is enrolled
    if not Enrollment.objects.filter(student=request.user, course=course).exists():
        messages.error(request, 'You need to enroll in this course first!')
        return redirect('course_detail', course_id=course_id)
    
    threads = course.discussion_threads.all()
    thread_form = DiscussionThreadForm()

    if request.method == 'POST':
        thread_form = DiscussionThreadForm(request.POST)
        if thread_form.is_valid():
            thread = thread_form.save(commit=False)
            thread.course = course
            thread.author = request.user
            thread.save()
            messages.success(request, 'Discussion thread created successfully!')
            return redirect('course_discussions', course_id=course_id)

    return render(request, 'courses/course_discussions.html', {
        'course': course,
        'threads': threads,
        'thread_form': thread_form,
    })    


@login_required
def discussion_thread(request, course_id, thread_id):
    course = get_object_or_404(Course, id=course_id)
    thread = get_object_or_404(DiscussionThread, id=thread_id, course=course)

    # Check if  the user is enrolled 
    if not Enrollment.objects.filter(student=request.user, course=course).exists():
        messages.error(request, 'You need to enroll in this course first!')
        return redirect('course_detail', course_id=course_id)
    
    reply_form = DiscussionReplyForm()

    if request.method == 'POST':
        if thread.is_locked:
            messages.error(request, 'This discussion thread is locked.')
            return redirect('discussion_thread', course_id=course_id, thread_id=thread_id)
        
        reply_form = DiscussionReplyForm(request.POST)
        if reply_form.is_valid():
            reply = reply_form.save(commit=False)
            reply.thread = thread
            reply.author = request.user
            reply.save()
            messages.success(request, 'Reply posted successfully')
            return redirect('discussion_thread', course_id=course_id, thread_id=thread_id)
        
    return render(request, 'courses/discussion_thread.html', {
            'course': course,
            'thread': thread,
            'replies': thread.replies.all(),
            'reply_form': reply_form,
    })
    

@login_required
def mark_as_answer(request, course_id, thread_id, reply_id):
    course = get_object_or_404(Course, id=course_id)
    thread = get_object_or_404(DiscussionThread, id=thread_id, course=course)
    reply = get_object_or_404(DiscussionReply, id=reply_id, thread=thread)

    # Check if the user is thrad author or instructor
    if request.user != thread.author and request.user != course.instructor:
        messages.error(request, 'You do not have the permission to mark the answers.')
        return redirect('discussion_thread', course_id=course_id, thread_id=thread_id)
    
    # Toggle answer status
    reply.is_answer = not reply.is_answer
    reply.save()

    action = "marked as answer" if reply.is_answer else "unmarked as answer"
    messages.success(request, f'Reply {action} succssfully!')

    return redirect('discussion_thread', course_id=course_id, thread_id=thread_id)


@login_required
def add_rating(request, course_id):
    """Add or update course rating"""
    course = get_object_or_404(Course, id=course_id)

    if request.method == 'POST':
        form = RatingForm(request.POST)
        if form.is_valid():
            rating, created = Rating.objects.get_or_create(
                course=course,
                user=request.user,
                defaults={
                    'rating': form.cleaned_data['rating'],
                    'review': form.cleaned_data['review']
                }
            )
            if not created:
                rating.rating = form.cleaned_data['rating']
                rating.review = form.cleaned_data['review']
                rating.save()

            messages.success(request, 'Thank You for rating')
        else:
            messages.error(request, 'Invalid rating form')

    return redirect('course_detail', course_id=course_id) 


@login_required
def learning_path_list(request):
    """List all learning paths"""
    paths = LearningPath.objects.filter(is_published=True)

    # Filter by category
    category = request.GET.get('category', '')
    if category:
        paths = paths.filter(category__slug=category)

    # Filter by level
    level = request.GET.get('level', '')
    if level:
        paths = paths.filter(level=level)

    context = {
        'paths': paths,
        'categories': Category.objects.all(),
    }    
    return render(request, 'courses/learning_path_list.html', context)


@login_required
def learning_path_detail(request, slug):
    """View learning path detail"""
    path = get_object_or_404(LearningPath, slug=slug, is_published=True)

    # Get or create enrollment
    enrollment, created = LearningPathEnrollment.objects.get_or_create(
        user=request.user,
        path=path
    )

    if not created:
        enrollment.calculate_progress()

    context = {
        'path': path,
        'enrollment': enrollment,
    }    
    return render(request, 'courses/learning_path_detail.html', context)


@login_required
def enroll_learning_path(request, slug):
    """Enroll in a learning path"""
    path = get_object_or_404(LearningPath, slug=slug, is_published=True)

    enrollment, created = LearningPathEnrollment.objects.get_or_create(
        user=request.user,
        path=path
    )

    if created:
        messages.success(request, f"Successfully enrolled in {path.title}!")

        # Auto enroll in courses in that path
        for path_course in path.path_courses.all():
            Enrollment.objects.get_or_create(
                student=request.user,
                course=path_course.course
            )

        # Send notification
        try:
            EmailService.send_enrollment_email(request.user, path)
        except:
            pass
    else:
        messages.info(request, f"You're already enrolled in {path.title}.")

    return redirect('learning_path_detail', slug=slug)


@login_required
def toggle_bookmark(request, lesson_id):
    """Toggle bookmark for a lesson"""
    lesson = get_object_or_404(Lesson, id=lesson_id)

    bookmark, created = Bookmark.objects.get_or_create(
        user=request.user,
        lesson=lesson
    )

    if not created:
        bookmark.delete()
        message = f"Removed bookmark form {lesson.title}"
        bookmarked = False
    else:
        message = f"Added bookmark for {lesson.title}"
        bookmarked = True

    if request.headers.get('x-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'bookmarked': bookmarked,
            'message': message
        })        
    
    messages.success(request, message)
    return redirect('lesson_detail', course_id=lesson.module.course.id, lesson_id=lesson.id)


@login_required
def my_bookmarks(request):
    """View all user bookmarks"""
    bookmarks = Bookmark.objects.filter(user=request.user)

    context = {
        'bookmarks': bookmarks,
    }

    return render(request, 'courses/my_bookmarks.html', context)


@login_required
def my_progress(request):
    """view user progress analytics"""
    progress_data = AnalyticsService.get_user_progress(request.user)

    # Get recent activities
    recent_lessons = LessonProgress.objects.filter(
        student=request.user
    ).order_by('-completed_at')[:10]

    recent_quizzes = QuizAttempt.objects.filter(
        student=request.user
    ).order_by('-completed_at')[:10]

    context = {
        'progress_data': progress_data,
        'recent_lessons': recent_lessons,
        'recent_quizzes': recent_quizzes,
    }

    return render(request, 'courses/my_progress.html', context)


@login_required
def course_analytics(request, course_id):
    """View analytics for a specific course (instructor only)"""
    course = get_object_or_404(Course, id=course_id)

    # Check if user is instructor or admin
    if request.user != course.instructor and not request.user.is_superuser:
        messages.error(request, "You don't have perimission to view this analytics.")
        return redirect('course_detail', course_id=course_id)
    
    analytics = AnalyticsService.get_course_anaytics(course)

    context = {
        'course': course,
        'analytics': analytics,
    }

    return render(request, 'courses/course_analytics.html', context)


@login_required
def platform_analytics(request):
    """View platform wide analytics (for admin)"""
    if not request.user.is_superuser:
        messages.error(request, "You don't have permission to view platform analytics")
        return redirect('home')
    
    analytics = AnalyticsService.get_platform_statistics()

    context = {
        'analytics': analytics,
    }

    return render(request, 'courses/paltform_analytics.html', context)


@login_required
def initiate_payment(request, course_id):
    """Initiate payment for a course"""
    course = get_object_or_404(Course, id=course_id)

    if course.price == 0:
        return redirect('enroll_course', course_id=course_id)
    
    payment_service = LemonSqueezyPaymentService()

    try:
        checkout_url = payment_service.create_checkout(request, course)
        if checkout_url:
            return redirect(checkout_url)
        else:
            messages.error(request, 'Failed to initiate payment. Please try again.')
            return redirect('course_detail', course_id=course_id)
    except Exception as e:
        messages.error(request, f'Payment error: {str(e)}')
        return redirect('course_detail', course_id=course_id)


@login_required
def payment_success(request, course_id):
    """Payment success page"""
    course = get_object_or_404(Course, id=course_id)

    # Check if payemnt is successfull and user is enrolled
    enrollment = Enrollment.objects.filter(
        student=request.user,
        course=course
    ).first()

    if not enrollment:
        messages.warning(request, 'Your enrollment is being processed. You will be enrolled shortly.')
        return redirect('course_detail', course_id=course_id)
    
    messages.success(request, f'Payment successfull. You are now enrolled in {course.title}.')
    return redirect('course_dashboard', course_id=course_id)


@login_required
def payment_cancel(request, course_id):
    """Payment cancel page"""
    course = get_object_or_404(Course, id=course_id)
    messages.info(request, 'Payment was cancelled. You can try again whenever you are ready.')
    return redirect('course_detail', course_id=course_id)


def lemon_squeezy_webhook(request):
    """Handle lemon squeezy webhooks"""
    payment_service = LemonSqueezyPaymentService()
    success, message = payment_service.handle_webhook(request)

    if success:
        return JsonResponse({'status': 'success', 'message': message})
    else:
        return JsonResponse({'status': 'error', 'message': message}, status=400)
    

def home_view(request):
    """
    Home page view with statistics, featured courses, and categories
    """
    # Get featured courses (published with highest rating or most popular)
    featured_courses = Course.objects.filter(
        is_published=True
    ).annotate(
        enrollment_count=Count('enrollments')
    ).order_by(
        '-average_rating', '-enrollment_count'
    )[:6]

    # If courses with rating, get latest published courses
    if not featured_courses:
        featured_courses = Course.objects.filter(
            is_published=True
        ).order_by('-created_at')[:6]

    # Get all published courses statistics
    published_courses = Course.objects.filter(is_published=True)

    # Platform statics
    total_courses = published_courses.count()
    total_students = User.objects.filter(
        profile__user_type='student'
    ).count()

    # Count unique instructors or have publised courses
    total_instructors = User.objects.filter(
        courses_taught__is_published=True
    ).distinct().count()

    # Count total lessons across all published courses
    total_lessons = 0
    for course in published_courses:
        total_lessons += course.modules.aggregate(
            lesson_count=Count('lessons')
        )['lesson_count'] or 0

    # Get categories with course count with display
    categories = Category.objects.annotate(
        course_count=Count('courses', filter=models.Q(courses__is_published=True))
    ).filter(
        course_count__gt=0
    ).order_by('-course_count')[:6]

    # Get popular lerning path
    learning_paths = LearningPath.objects.filter(
        is_published=True
    ).annotate(
        enrollment_count=Count('enrollments')
    ).order_by('-enrollment_count')[:3]

    # Get recent enrollments count (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_enrollmenst = Enrollment.objects.filter(
        enrolled_at__gte=thirty_days_ago
    ).count()

    # Get top instructors (by course count rating)
    top_instructors = User.objects.filter(
        courses_taught__is_published=True
    ).annotate(
        course_count=Count('courses_taught'),
        avg_rating=Avg('courses_taught__average_rating')
    ).order_by(
        '-course_count', '-avg_rating'
    )[:4]

    # Check if user is authenticated for personalized content
    if request.user.is_authenticated:
        # Get user''s enrolled courses for count
        user_enrollments = request.user.enrollments.values_list('course_id', flat=True)

        # Recommended courses from same categories as enrolled courses
        enrolled_categories = Course.objects.filter(
            id__in=user_enrollments
        ).values_list('category', flat=True).distinct()

        recommended_courses = Course.objects.filter(
            is_punlished=True,
            category__in=enrolled_categories
        ).exclude(
            id__in=user_enrollments
        ).annotate(
            enrollment_count=Count('enrollments')
        ).order_by('-average_rating', '-enrollment_count')[:4]

        # Get user's progress stats
        total_completed_lessons = request.user.lesson_progress.filter(
            completed=True
        ).count()

        user_course_completion = Enrollment.objects.filter(
            student=request.user,
            completed=True
        ).count()

        # Get user's achievements if gamification is enabled
        user_achievements = getattr(request.user, 'achievements', None)
        if user_achievements:
            total_achievements = user_achievements.count()
            recent_achievements = user_achievements.order_by('-created_at')[:3]
        else:
            total_achievements = 0
            recent_achievements = []

        # Get user's upcoming lessons (in progress)
        in_progress_lessons = request.user.lesson_progress.filter(
            completed=False
        ).select_ralted('lesson__module__course')[:5]

        context = {
            'featured_courses': featured_courses,
            'total_courses': total_courses,
            'total_students': total_students,
            'total_instructors': total_instructors,
            'total_lessons': total_lessons,
            'categories': categories,
            'learning_paths': learning_paths,
            'recent_enrollmets': recent_enrollmenst,
            'top_instructors': top_instructors,
            'recommended_courses': recommended_courses if request.user.is_authenticated else [],
            'user_enrolled_count': request.user.enrollments.count() if request.user.is_authenticated else 0,
            'user_completed_courses': user_course_completion if request.user.is_authenticated else 0,
            'user_completed_lessons': total_completed_lessons if request.user.is_authenticated else 0,
            'total_achievements': total_achievements if request.user.is_authenticated else 0,
            'recent_achievements': recent_achievements if request.user.is_authenticated else [],
            'in_progress_lessons': in_progress_lessons if request.user.is_authenticated else [],         
        }     
    else:
        context = {
            'featured_courses': featured_courses,
            'total_courses': total_courses,
            'total_students': total_students,
            'total_instructors': total_instructors,
            'total_lessons': total_lessons,
            'categories': categories,
            'learning_paths': learning_paths,
            'recent_enrollments': recent_enrollmenst,
            'top_instructors': top_instructors,
            'recommended_courses': [],
            'user_enrolled_count': 0,
            'user_completed_courses': 0,
            'user_completed_lessons': 0,
            'total_achievements': 0,
            'recent_achievements': [],
            'in_progress_lessons': [],
        }    

    return render(request, 'home.html', context)    