from django import forms
from .models import Calendar
from django.contrib.auth.models import User

class CalendarUploadForm(forms.ModelForm):
    class Meta:
        model = Calendar
        fields = ["name", "ics_file"]
    