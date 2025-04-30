from django import forms

# from .models import Event

class CalendarUploadForm(forms.Form):
    name = forms.CharField(max_length=255)
    ics_file = forms.FileField()
