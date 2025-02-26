from django.db import models
from django.contrib.auth.models import AbstractUser

from PIL import Image

# Create your models here.
class CustomUser(AbstractUser):
    profile_picture = models.ImageField(default="profile_images/default_user_profile_picture.png", upload_to="profile_images/")
    profile_bio = models.TextField()

    def save(self, *args, **kwargs):
        super().save()

        img = Image.open(self.profile_picture.path)

        if img.height > 100 or img.width > 100:
            new_img = (100, 100)
            img.thumbnail(new_img)
            img.save(self.profile_picture.path)
