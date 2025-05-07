from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import StudySession
from notifications.models import Notification

@receiver(post_save, sender=StudySession)
def notify_user_on_study_session_create(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            user=instance.host,  # Assuming created_by is the user who created the session
            message=f"Your study session, {instance.title}, was created successfully!"
        )
