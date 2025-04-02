from django.db import models
from users.models import CustomUser

from datetime import datetime

# Create your models here.
class Calendar(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="calendars")
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username + " - " + self.name

class Event(models.Model):

    class Types(models.TextChoices):
        EVENT = "event", "Event"
        STUDY = "study", "Study"

    calendar = models.ForeignKey(Calendar, on_delete=models.CASCADE)
    title = models.TextField()
    start = models.DateTimeField()
    end = models.DateTimeField(null=True, blank=True)
    duration = models.DurationField(null=True, blank=True)
    description = models.TextField(blank=True)
    rrule = models.TextField(blank=True, null=True)
    type = models.CharField(max_length=10, choices=Types.choices)


    def save(self, *args, **kwargs):
        # Ensure start and end are datetime objects
        if isinstance(self.start, str):
            from django.utils.dateparse import parse_datetime
            self.start = parse_datetime(self.start)  # Convert string to datetime

        if isinstance(self.end, str):
            from django.utils.dateparse import parse_datetime
            self.end = parse_datetime(self.end)  # Convert string to datetime

        # Calculate duration if end is provided
        if self.end and self.start:
            self.duration = self.end - self.start

        super().save(*args, **kwargs)
