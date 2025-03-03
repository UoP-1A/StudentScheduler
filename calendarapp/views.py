from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.timezone import make_aware

from .forms import CalendarUploadForm
from .models import Calendar, Event

from rest_framework.decorators import api_view
from json import dumps

from icalendar import Calendar as ICalCalendar
from datetime import datetime
from dateutil.rrule import rrulestr

# Create your views here.
def index(request):
    return render(request, "calendarapp/calendar.html")

@login_required
def upload_calendar(request):
    """
    This view is called when you upload a calendar through the upload form. It will store the calendar ICS file.
    It then processes this file to its events, and stores them in the database using the Event model.
    """
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
    """
    This function opens the uploaded ICS file, iterates through each event,
    and creates an event object to store in the database.
    """
    with open(file_path, 'rb') as f:
        calendar = ICalCalendar.from_ical(f.read())

        for component in calendar.walk():
            if component.name == "VEVENT":
                title = str(component.get("SUMMARY", "Untitled Event"))[:255]
                start = component.get("DTSTART").dt.isoformat()
                end = component.get("DTEND").dt.isoformat() if component.get("DTEND") else None
                description = str(component.get("DESCRIPTION", ""))[:1000]

                # Handle recurring events (rrule)
                rrule = component.get("RRULE")

                rrule_str = None
                if rrule:
                    rrule_str = rrulestr(rrule.to_ical().decode('utf-8'), dtstart=component.get("DTSTART").dt)  # Convert rrule to string

                event = Event(
                    calendar = user_calendar,
                    title = title,
                    start = start,
                    end = end,
                    description = description,
                    rrule = rrule_str
                )
                event.save()

@login_required
@api_view(['GET'])
def prep_events(request):
    """
    This function loops over the list of calendar events and handles rrules for repetition.
    They are then returned in a JsonResponse to the frontend FullCalendar.
    """
    user = request.user
    events = Event.objects.filter(calendar__user=user)

    event_list = []
    for e in events:
        event_data = {
            "id": e.id,
            "title": e.title,
            "start": e.start.isoformat(),
            "end": e.end.isoformat() if e.end else None,
            "description": e.description,
        }

        # Add rrule if it exists
        if e.rrule:
            event_data["rrule"] = e.rrule

        event_list.append(event_data)

    return JsonResponse(event_list, safe=False, encoder=DjangoJSONEncoder)

@login_required
@api_view(['POST'])
def delete_calendar(request, calendar_id):
    """
    When a user deletes a calendar from their profile, this view is caleld to handle the deletion of the calendar file and its events.
    """
    calendar = get_object_or_404(Calendar, id=calendar_id, user=request.user)

    calendar.ics_file.delete()
    calendar.delete()
    messages.success(request, "Calendar deleted successfully.")

    return redirect("profile")
