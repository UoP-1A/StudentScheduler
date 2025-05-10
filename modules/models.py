from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator

from users.models import CustomUser

# Create your models here.

class Module(models.Model):
    user = models.ForeignKey(CustomUser, related_name="modules", on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    credits = models.IntegerField(default=0)

    def overall_grade(self):
        grades = self.grades.all()
        if not grades:
            return None
        total_weight = sum(grade.weight for grade in grades)
        if total_weight == 0:
            return None
        weighted_sum = sum(grade.mark * grade.weight for grade in grades)
        return round(weighted_sum / total_weight, 2)

    def save(self, *args, **kwargs):
        if (self.user.modules.count() >= 6 or self.user.modules.count() <= -1) and not self.pk:
            raise ValidationError("A user can only have between 0 and 6 modules inclusive.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name}"

class Grade(models.Model):
    module = models.ForeignKey(Module, related_name="grades", on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    mark = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)]
    )
    weight = models.FloatField(
        validators=[MinValueValidator(0.0)]
    )

    def clean(self):
        if self.weight < 0:
            raise ValidationError("Weight cannot be negative.")
        if self.mark < 0 or self.mark > 100:
            raise ValidationError("Mark must be between 0 and 100.")
        
        total_weight = sum(
            grade.weight for grade in self.module.grades.exclude(pk=self.pk)
        ) + self.weight

        if total_weight > 100:
            raise ValidationError("This exceeds the total allowed weight of 100.")

    def save(self, *args, **kwargs):
        self.full_clean()  # Runs clean() and other validations
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Assessment: {self.name} Mark: {self.mark}"