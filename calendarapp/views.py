from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.contrib import messages

from .forms import CalendarUploadForm
from .models import Calendar, Event

from rest_framework.decorators import api_view

from common.util import preprocess_ics, processRrule

from icalendar import Calendar as ICalCalendar
from json import dumps
from datetime import datetime


# Create your views here.
def index(request):
    return render(request, "calendarapp/calendar.html")

@login_required
def upload_calendar(request):
    if request.method == "POST":
        form = CalendarUploadForm(request.POST, request.FILES)
        if form.is_valid():
            calendar = form.save(commit=False)
            calendar.user = request.user
            calendar.save()

            parse_ics(calendar.ics_file.path, calendar)
            return redirect(to="/")
    else:
        form = CalendarUploadForm
    return render(request, "calendarapp/upload_calendar.html", {"form": form})

def parse_ics(file_path, user_calendar):
    with open(file_path, 'rb') as f:
        calendar = ICalCalendar.from_ical(f.read())

        for component in calendar.walk():
            if component.name == "VEVENT":
                event = Event(
                    calendar=user_calendar,
                    title=str(component.get('summary', 'Untitled Event'))[:255], # Only ensure first 255 characters.
                    start=component.get('dtstart').dt if isinstance(component.get('dtstart').dt, datetime) else component.get('dtstart').dt,
                    end=component.get('dtend').dt if isinstance(component.get('dtend').dt, datetime) else component.get('dtend').dt
                )
                event.save()

@login_required
@api_view(['GET'])
def prep_events(request):
    """
    This function loops over the list of calendar events, and handles rrules for repetition.
    """
    all_events = []

    calendars = Calendar.objects.all()

    for calendar in calendars:
        ics_path = calendar.ics_file.path
        if default_storage.exists(ics_path):
            ics_content = preprocess_ics(ics_path)
            parsed_calendar = ICalCalendar.from_ical(ics_content)
            events = processRrule(parsed_calendar)
            all_events.extend(events)

    return HttpResponse(dumps(all_events), content_type="application/json")

@login_required
@api_view(['POST'])
def delete_calendar(request, calendar_id):
    calendar = get_object_or_404(Calendar, id=calendar_id, user=request.user)

    calendar.ics_file.delete()
    calendar.delete()
    messages.success(request, "Calendar deleted successfully.")

    return redirect("profile")
