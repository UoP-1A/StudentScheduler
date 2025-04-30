from django.db import models
from users.models import CustomUser
from calendarapp.models import Calendar

class StudySession(models.Model):
    host = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="study_sessions")
    participants = models.ManyToManyField(CustomUser, related_name="study_sessions_joined", blank=True)
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
        return self.user.username + " - " + StudySession.title + " x " + str(self.recurrence_amount)