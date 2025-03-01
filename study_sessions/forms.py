from django import forms
from .models import StudySession

class StudySessionForm(forms.ModelForm):
    class Meta:
        model = StudySession
        fields = ['participants', 'title', 'description', 'start_time', 'end_time', 'date', 'is_recurring']
        widgets = {
            'participants': forms.TextInput(attrs={'placeholder': 'Participants'}),
            'title': forms.TextInput(attrs={'placeholder': 'Title'}),
            'description': forms.Textarea(attrs={'placeholder': 'Description'}),
            'start_time': forms.DateTimeInput(attrs={'placeholder': 'Start Time'}),
            'end_time': forms.DateTimeInput(attrs={'placeholder': 'End Time'}),
            'date': forms.DateInput(attrs={'placeholder': 'Date'}),
            'is_recurring': forms.CheckboxInput(attrs={'placeholder': 'Recurring'}),
        }