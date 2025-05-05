from django.db import models
from users.models import CustomUser
from calendarapp.models import Calendar

#notifications code

from django.db.models.signals import post_save
from django.dispatch import receiver
from notifications.models import Notification


class StudySession(models.Model):
    host = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="study_sessions")
    #participants = models.ManyToManyField(CustomUser, related_name="study_sessions_joined", blank=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    date = models.DateField()
    is_recurring = models.BooleanField(default=False)
    calendar_id = models.ForeignKey(Calendar, on_delete=models.CASCADE, related_name="study_sessions")
    #module

    def __str__(self):
        return self.user.username + " - " + self.title
    
class RecurringStudySession(models.Model):
    session_id = models.ForeignKey(StudySession, on_delete=models.CASCADE, related_name="recurring_sessions")
    recurrence_amount = models.IntegerField()

    def __str__(self):
        return self.session_id.host.username + " - " + self.session_id.title + " x " + str(self.recurrence_amount)
    
class StudySessionParticipant(models.Model):
    study_session = models.ForeignKey(StudySession, on_delete=models.CASCADE, related_name="participants_set")
    participant = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="study_sessions_participated")

    def __str__(self):
        return self.participant.username + " - " + self.study_session.title
    
#notifications code

@receiver(post_save, sender=StudySessionParticipant)
def create_join_notification(sender, instance, created, **kwargs):
    if created:
        session = instance.study_session
        participant = instance.participant
        host = session.host

        # Only notify if host isn't the participant themselves
        if host != participant:
            Notification.objects.create(
                user=host,
                message=f"{participant.username} joined your study session '{session.title}'"
            )