from django.db import models
from users.models import CustomUser


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
    description = models.TextField(blank=True)
    rrule = models.TextField(blank=True, null=True)
    type = models.CharField(max_length=10, choices=Types.choices)
