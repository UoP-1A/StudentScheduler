from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from .models import Notification

@login_required
def notifications_view(request):
    notificationsList = Notification.objects.filter(user=request.user).order_by('timestamp')
    return render(request, 'notifications/notifications.html', {'notificationsList': notificationsList})

@require_POST
@login_required
def mark_as_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return redirect('notifications')