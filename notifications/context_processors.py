from .models import Notification

def notifications(request):
    if request.user.is_authenticated:
        return {
            'notifications': Notification.objects.filter(user=request.user, is_read=False).order_by('-timestamp')[:5],  # Last 5 notifications
            'unread_count': Notification.objects.filter(user=request.user, is_read=False).count()
        }
    return {}