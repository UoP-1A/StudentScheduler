from django.db import models
from django.core.exceptions import ValidationError

from users.models import CustomUser

# Create your models here.

class Module(models.Model):
    user = models.ForeignKey(CustomUser, related_name="modules", on_delete=models.CASCADE)
    name = models.CharField(max_length=50)

    def overall_grade(self):
        grades = self.grades.all()
        if not grades:
            return None
        total_weight = sum(grade.weight for grade in grades)
        if total_weight == 0:
            return None
        weighted_sum = sum(grade.grade * grade.weight for grade in grades)
        return round(weighted_sum / total_weight, 2)

    def save(self, *args, **kwargs):
        if self.user.modules.count() >= 6 and not self.pk:
            raise ValidationError("A user cannot have more than 6 modules.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} (User: {self.user.username})"

class Grade(models.Model):
    module = models.ForeignKey(Module, related_name="grades", on_delete=models.CASCADE)
    grade = models.FloatField()
    weight = models.FloatField()

    def __str__(self):
        return f"Mark: {self.grade} Module: {self.module.name}"