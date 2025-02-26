from django import forms
from .models import Calendar
from django.contrib.auth.models import User
from datetime import datetime
from django.test import TestCase

class CalendarUploadForm(forms.ModelForm):
    class Meta:
        model = Calendar
        fields = ["name", "ics_file"]
    
class Event:
    def __init__(self, name, date, description=""):
        self.name = name
        self.date = date  
        self.description = description

    def __str__(self):
        description_text = f"\nDescription: {self.description}" if self.description else ""
        return f"Event: {self.name}\nDate: {self.date.strftime('%d-%m-%Y')}{description_text}\n"

class EventManager:
    def __init__(self):
        self.events = []

    def create_event(self, name, date, description=""):
        event = Event(name, date, description)
        self.events.append(event)
        print(f"Event '{name}' created successfully.")

    def delete_event(self, name):
        for event in self.events:
            if event.name == name:
                self.events.remove(event)
                print(f"Event '{name}' deleted successfully.")
                return
        print(f"Event '{name}' not found.")

    def edit_event(self, name, new_name=None, new_date=None, new_description=None):
        for event in self.events:
            if event.name == name:
                if new_name:
                    event.name = new_name
                if new_date:
                    event.date = new_date
                if new_description is not None:  # Allow empty description
                    event.description = new_description
                print(f"Event '{name}' updated successfully.")
                return
        print(f"Event '{name}' not found.")

    def list_events(self):
        if not self.events:
            print("No events found.")
        else:
            for event in self.events:
                print(event)
