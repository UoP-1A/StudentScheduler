from django.db import models
from users.models import CustomUser


# Create your models here.
class Calendar(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="calendars")
    name = models.CharField(max_length=255)
    ics_file = models.FileField(upload_to="calendars/")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username + " - " + self.name

class CalendarEvent(models.Model):
    title = models.CharField(max_length=200)
    start = models.DateTimeField()
    end = models.DateTimeField(null=True, blank=True)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=255, blank=True)
    ical_uid = models.CharField(max_length=255, unique=True)
    is_recurring = models.BooleanField(default=False)
    rrule = models.TextField(blank=True, null=True)
    exdates = models.JSONField(blank=True, null=True) 
    duration = models.DurationField(null=True) 