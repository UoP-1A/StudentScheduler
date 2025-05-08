from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

from users.models import CustomUser
from calendarapp.models import Calendar

class StudySession(models.Model):
    host = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="study_sessions")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    date = models.DateField()
    is_recurring = models.BooleanField(default=False)
    calendar_id = models.ForeignKey(Calendar, on_delete=models.CASCADE, related_name="study_sessions")

    def __str__(self):
        return f"{self.host.username} - {self.title}"  # Fixed: changed self.user to self.host

    def clean(self):
        """Add validation for time and date logic"""
        # Date validation
        if self.date < timezone.now().date():
            raise ValidationError("Study session date cannot be in the past")
        
        # Time validation
        if self.end_time <= self.start_time:
            raise ValidationError("End time must be after start time")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
class RecurringStudySession(models.Model):
    session_id = models.ForeignKey(StudySession, on_delete=models.CASCADE, related_name="recurring_sessions")
    recurrence_amount = models.PositiveIntegerField()

    def clean(self):
        """Add validation for recurrence_amount"""
        if self.recurrence_amount <= 0:
            raise ValidationError("Recurrence amount must be a positive number")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.session_id.host.username} - {self.session_id.title} x {self.recurrence_amount}"
    
class StudySessionParticipant(models.Model):
    study_session = models.ForeignKey(
        StudySession, 
        on_delete=models.CASCADE,
        related_name="participants_set"
    )
    participant = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="study_sessions_participated"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['study_session', 'participant'],
                name='unique_participation'
            )
        ]

    def __str__(self):
        return f"{self.participant.username} - {self.study_session.title}"

    def clean(self):
        """Additional validation"""
        
        # Check for existing participation (excluding current instance if updating)
        existing = StudySessionParticipant.objects.filter(
            study_session=self.study_session,
            participant=self.participant
        )
        if self.pk:
            existing = existing.exclude(pk=self.pk)
        if existing.exists():
            raise ValidationError("This user is already participating in this session")

    def save(self, *args, **kwargs):
        """Only run clean() for new instances to allow constraint to handle duplicates"""
        if not self.pk:
            self.full_clean()
        super().save(*args, **kwargs)