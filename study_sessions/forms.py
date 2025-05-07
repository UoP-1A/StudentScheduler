from django import forms
from .models import StudySession, RecurringStudySession
from users.models import CustomUser
from calendarapp.models import Calendar

class AutoStudySessionForm(forms.ModelForm):
    participants = forms.ModelMultipleChoiceField(
        queryset=CustomUser.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Participants"
    )

    class Meta:
        model = StudySession
        fields = ['participants','title', 'description', 'is_recurring', 'calendar_id']
        exclude = ['host', 'start_time', 'end_time', 'date']


class ManualStudySessionForm(forms.ModelForm):
    participants = forms.ModelMultipleChoiceField(
        queryset=CustomUser.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Participants"
    )

    class Meta:
        model = StudySession
        fields = ['participants','title', 'description', 'start_time', 'end_time', 'date', 'is_recurring', 'calendar_id']
        exclude = ['host']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }

class RecurringSessionForm(forms.ModelForm):

    class Meta:
        model = RecurringStudySession
        fields = ['recurrence_amount']
        widgets = {
            'recurrence_amount': forms.NumberInput(attrs={'class': 'form-control'}),
        }