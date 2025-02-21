from django.db import models
from django.contrib.auth.models import User


# Create your models here.
class Calendar(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="calendars")
    name = models.CharField(max_length=255)
    ics_file = models.FileField(upload_to="calendars/")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username + " - " + self.name