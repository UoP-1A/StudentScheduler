from django import forms
from .models import Calendar
from django.contrib.auth.models import User
from datetime import datetime
from django.test import TestCase

# from .models import Event


class CalendarUploadForm(forms.Form):
    name = forms.CharField(max_length=255)
    ics_file = forms.FileField()