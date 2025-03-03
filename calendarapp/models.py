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

class Event(models.Model):
    calendar = models.ForeignKey(Calendar, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    start = models.DateTimeField()
    end = models.DateTimeField(null=True, blank=True)
    description = models.TextField(blank=True)
    rrule = models.TextField(blank=True, null=True)