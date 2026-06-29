from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Course, Enrollment, Lesson, QuizAttempt, Quiz, UserAnswer, Certificate, DiscussionReply, DiscussionThread, LessonProgress
from .forms import UserAnswerForm, DiscussionThreadForm, DiscussionReplyForm
from django.utils import timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
from reportlab.lib import colors
from django.http import HttpResponse











def course_list(request):
    courses = Course.objects.filter(is_published=True)
    return render(request, 'courses/course_list.html', {'courses': courses})


def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    is_enrolled = False
    if request.user.is_authenticated:
        is_enrolled = Enrollment.objects.filter(student=request.user, course=course).exists()

    return render(request,'courses/course_detail.html', {
        'course': course,
        'is_enrolled': is_enrolled
    })


@login_required
def enroll_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    # To check if the user is already enrolled
    if Enrollment.objects.filter(student=request.user, course=course,).exists():
        messages.warning(request, 'You are already enrolled in this course')
    else:
        Enrollment.objects.create(student=request.user, course=course)
        messages.success(request, f'Successfully enrolled in {course.title}!')

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
        messages.success(request, f"Congragulation! You've completed {course.title}! 🎉")

    # To check if the certificate even exists
    has_certificate = Certificate.objects.filter(student=request.user, course=course).exists()    

    return render(request, 'courses/course_dashboard.html', {
        'course': course,
        'enrollment': enrollment,
        'has_certificate': has_certificate
    })       


@login_required
def lesson_detail(request, course_id, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id, module__course_id=course_id)
    course = lesson.module.course

    # Check if the user is enrolled
    if not Enrollment.objects.filter(student=request.user, course=course,).exists():
        messages.error(request, 'You need to enroll in this course first')
        return redirect('course_detail', course_id=course_id)
    
    # Get or create lesson progress
    lesson_progress, created = LessonProgress.objects.get_or_create(student=request.user, lesson=lesson)


    # Mark as completed when user visits the given course or you can add a complete button
    if not lesson_progress.completed:
        lesson_progress.completed = True
        lesson_progress.completed_at = timezone.now()
        lesson_progress.save()
        messages.success(request, "Lesson marked as completed!")


    return render(request, 'courses/lesson_detail.html', {
        'lesson' : lesson,
        'course' : course,
        'lesson_progress' : lesson_progress

    })


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
