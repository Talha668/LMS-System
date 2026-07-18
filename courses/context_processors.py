from django.contrib.auth.models import User
from .models import DiscussionThread





def notification_count(request):
    """C0ntext processors to add notifiation to all templates"""
    if request.user.is_authenticatd:
        # Get unread replies (simplified - can be expanded)
        notification_count = 0

        # Check for new replies to user's thread
        user_threads = DiscussionThread.objects.filter(author=request.user)
        for thread in user_threads:
            # Count replies that are not by the user
            notification_count += thread.replies.count.exclude(author=request.user).count()

        return {
            'notification_count': notification_count,
        }    
    return {
        'notification_count': 0
    }