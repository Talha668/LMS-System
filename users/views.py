from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth import login, authenticate
from .forms import CustomUserCreationForm
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from .forms import CustomUserCreationForm, ProfileForm, UserProfileForm
from .models import Profile
from courses.models import Enrollment, Certificate










def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome {user.get_full_name()}! Your account has been created.')
            
            # Send welcome email
            try:
                send_mail(
                    'Welcome to LMS Learning Platform!',
                    f'Dear {user.get_full_name()}, \n\n'
                    f'Welcome to our Learning Management System! we\'re excited to have you onboard.\n\n'
                    f'You can now start exploring courses and leraning new skills.\n\n'
                    f'Best regards,\n\n'
                    f'The LMS Team',
                    settings.DEFAULT_FROM_EMAIL,
                    [user.eamil],
                    fail_silently=True,
                ) 
            except:
                pass

            return redirect('course_list')
    else:
        form = CustomUserCreationForm()

    return render(request, 'registration/register.html', {'form': form})


@login_required
def profile_view(request):
    """User profile view"""
    # Get user's course statistics
    total_courses = request.user.enrollment.count()
    completed_courses = request.user.enrollment.filter(completed=True).count()
    certificates = Certificate.objects.filter(student=request.user)
    total_lessons = request.user.lesson_progress.filter(completed=True).count()

    context = {
        'user': request.user,
        'profile': request.user.profile,
        'total_courses': total_courses,
        'completed_courses': completed_courses,
        'certificates': certificates,
        'total_lessons': total_lessons,
    }
    return render(request, 'users/profile.html', context)


@login_required
def profile_edit(request):
    """Edit user profile"""
    profile = request.user.profile

    if request.method =='POST':
        user_form = UserProfileForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('profile')
    else:
        user_form = UserProfileForm(instance=request.user)
        profile_form = ProfileForm(instance=profile)

    return render(request, 'user/profile_edits.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })


def home_view(request):
    """Home page view"""
    from courses.models import Course, Enrollment, Lesson

    featured_courses = Course.objects.filter(is_published=True)[:6]
    total_courses = Course.objects.filter(is_published=True).count()
    total_students = Enrollment.objects.values('student').distinct().count()
    total_instructors = Course.objects.values('instructor').distinct().count()
    total_lessons = Lesson.objects.count()

    #Get categories for filter
    categories = Course.objects.filter(is_published=True).values_list('category', flat=True).distinct()
    categories = [cat for cat in categories if cat]

    context = {
        'featured_courses': featured_courses,
        'total_courses': total_courses,
        'total_students': total_students,
        'total_instructors': total_instructors,
        'total_lessons': total_lessons,
        'categories': categories[:6],      # Show top 6 categories
    }
    return render(request, 'home.html', context)