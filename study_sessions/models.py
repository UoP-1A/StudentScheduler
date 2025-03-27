from django.db import models
from users.models import CustomUser
from calendarapp.models import Calendar

class StudySession(models.Model):
    host = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="study_sessions")
    participants = models.ManyToManyField(CustomUser, related_name="study_sessions_joined", blank=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    date = models.DateField()
    is_recurring = models.BooleanField(default=False)
    calendar_id = models.ForeignKey(Calendar, on_delete=models.CASCADE, related_name="study_sessions")
    #module

    def __str__(self):
        return self.user.username + " - " + self.title