from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import StudySessionParticipant
from notifications.models import Notification

@receiver(post_save, sender=StudySessionParticipant)
def create_join_notification(sender, instance, created, **kwargs):
    if created:
        session = instance.study_session
        participant = instance.participant
        host = session.host

        if host != participant:
            Notification.objects.create(
                user=host,
                message=f"{participant.username} joined your study session '{session.title}'"
            )
