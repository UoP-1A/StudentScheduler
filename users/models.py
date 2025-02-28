from django.db import models
from django.contrib.auth.models import AbstractUser

from PIL import Image

# Create your models here.
class CustomUser(AbstractUser):
    profile_picture = models.ImageField(default="profile_images/default_user_profile_picture.png", upload_to="profile_images/")
    profile_bio = models.TextField()
    friends = models.ManyToManyField("self", blank=True)

    def save(self, *args, **kwargs):
        super().save()

        img = Image.open(self.profile_picture.path)

        if img.height > 100 or img.width > 100:
            new_img = (100, 100)
            img.thumbnail(new_img)
            img.save(self.profile_picture.path)

class FriendRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'PENDING'),
        ('accepted', 'accepted'),
        ('rejected', 'rejected')
    )

    from_user = models.ForeignKey(
        CustomUser,
        related_name='sent_requests',
        on_delete=models.CASCADE
    )

    to_user = models.ForeignKey(
        CustomUser,
        related_name='received_requests',
        on_delete=models.CASCADE
    )

    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('from_user', 'to_user')

    def __str__(self):
        return f"{self.from_user} -> {self.to_user} ({self.status})"