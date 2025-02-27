from django import forms
from .models import Calendar
from django.contrib.auth.models import User
from datetime import datetime
from django.test import TestCase

from .models import Event


class CalendarUploadForm(forms.ModelForm):
    class Meta:
        model = Calendar
        fields = ["name", "ics_file"]
    

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['name', 'date', 'description']
