from django.db import models
from users.models import CustomUser
from django.core.exceptions import ValidationError

# Create your models here.
class Calendar(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="calendars")
    name = models.CharField(max_length=255, blank=False, null=False)
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
    type = models.CharField(max_length=10, choices=Types.choices, default=Types.EVENT)

    def clean(self):
        # Ensure start is set
        if not self.start:
            raise ValidationError("Start time must be set.")

        # Ensure end is after start if provided
        if self.end and self.end <= self.start:
            raise ValidationError("End time must be after the start time.")

        # Ensure duration is consistent with start and end
        if self.end and self.duration and self.duration != (self.end - self.start):
            self.end = self.start + self.duration


    def save(self, *args, **kwargs):
        # Ensure start and end are datetime objects
        if isinstance(self.start, str):
            from django.utils.dateparse import parse_datetime
            self.start = parse_datetime(self.start) 

        if isinstance(self.end, str):
            from django.utils.dateparse import parse_datetime
            self.end = parse_datetime(self.end)

        # Calculate duration if end is provided
        if self.end and self.start and not self.duration:
            self.duration = self.end - self.start

        self.full_clean()

        super().save(*args, **kwargs)
        