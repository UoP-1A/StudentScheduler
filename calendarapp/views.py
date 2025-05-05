from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.dateparse import parse_datetime
from django.core.exceptions import ValidationError

from .forms import CalendarUploadForm
from .models import Calendar, Event

from rest_framework.decorators import api_view
from icalendar import Calendar as ICalCalendar

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
    form = CalendarUploadForm(request.POST, request.FILES)
    if form.is_valid():
        name = form.cleaned_data["name"]
        ics_file = request.FILES["ics_file"]

        # Check file extension and return form with errors if invalid
        if not ics_file.name.endswith(".ics"):
            form.add_error("ics_file", "File must have .ics extension")
            return render(request, "calendarapp/upload_calendar.html", {"form": form})

        # Create calendar entry
        calendar = Calendar.objects.create(user=request.user, name=name)
        parse_ics(ics_file, calendar)
        return redirect("/")
    
    return render(request, "calendarapp/upload_calendar.html", {"form": form})

def parse_ics(file, user_calendar):
    """
    This function opens the uploaded ICS file, iterates through each event,
    and creates an event object to store in the database.
    """
    calendar = ICalCalendar.from_ical(file.read())

    for component in calendar.walk():
        if component.name == "VEVENT":
            title = str(component.get("SUMMARY", "Untitled Event"))
            start = component.get("DTSTART").dt.isoformat()
            end = component.get("DTEND").dt.isoformat() if component.get("DTEND") else None
            description = str(component.get("DESCRIPTION", ""))

            # Handle recurring events (rrule)
            rrule = component.get("RRULE")

            rrule_str = None
            if rrule:
                # Convert ical module rrule to fullcalendar readable string
                rrule_str = rrulestr(rrule.to_ical().decode('utf-8'), dtstart=component.get("DTSTART").dt)

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
            "type": e.type,
            "start": e.start.isoformat(),
            "end": e.end.isoformat() if e.end else None,
            "description": e.description,
        }

        # Add rrule if it exists
        if e.rrule:
            event_data["rrule"] = e.rrule
        if e.end:
            event_data["duration"] = str(e.duration) if e.duration else None

        event_list.append(event_data)

    return JsonResponse(event_list, safe=False, encoder=DjangoJSONEncoder)


@login_required
@api_view(['POST'])
def update_event(request):
    event_id = request.data.get('id')
    start_str = request.data.get('start')
    end_str = request.data.get('end')

    # Validate required fields
    if not event_id or not start_str:
        return JsonResponse({'status': 'error', 'message': 'Missing required fields'}, status=400)

    try:
        # Parse datetimes only if strings are provided
        new_start = parse_datetime(start_str)
        new_end = parse_datetime(end_str) if end_str else None

        event = Event.objects.get(id=event_id)
        if event.calendar.user != request.user:
            return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)

        event.start = new_start
        event.end = new_end
        event.save()
        return JsonResponse({'status': 'success', 'event_id': event_id})

    except ValueError as e:
        return JsonResponse({'status': 'error', 'message': f'Invalid datetime format: {str(e)}'}, status=400)
    except Event.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Event not found'}, status=404)

@login_required
@api_view(['POST'])
def delete_calendar(request, calendar_id):
    """
    When a user deletes a calendar from their profile, this view is caleld to handle the deletion of the calendar file and its events.
    """
    calendar = get_object_or_404(Calendar, id=calendar_id, user=request.user)

    calendar.delete()
    messages.success(request, "Calendar deleted successfully.")

    return redirect("profile")
