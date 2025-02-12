from django.shortcuts import render
from django.http import HttpResponse

from rest_framework.response import Response
from rest_framework.decorators import api_view

from icalendar import Calendar
from dateutil.rrule import rrulestr
from json import dumps

# Create your views here.
def index(request):
    return render(request, "calendarapp/calendar.html")

def preprocess_ics(file_path):
    """
    This function processes a calendar file, and returns the events as a list.
    """
    with open(file_path, "r") as f:
        lines = f.readlines()

    processed_lines = []
    categories_buffer = []

    for line in lines:
        if line.startswith("CATEGORIES:"):
            categories_buffer.append(line.strip())
        else:
            if categories_buffer:
                combined_categories = ",".join(
                    [cat.split(":", 1)[1] for cat in categories_buffer]
                )
                processed_lines.append(f"CATEGORIES:{combined_categories}\n")
                categories_buffer = []
            processed_lines.append(line)

    return "".join(processed_lines)

@api_view(['GET'])
def prep_events(request) -> list:
    """
    This function loops over the list of calendar events, and handles rrules for repetition.
    """
    global events
    ics_content = preprocess_ics("calendarTest.ics")

    calendar = Calendar.from_ical(ics_content)

    events = []
    for component in calendar.walk():
        if component.name == "VEVENT":
            event_data = {
                "title": str(component.get("SUMMARY")),
                "start": component.get("DTSTART").dt.isoformat(),
                "end": (
                    component.get("DTEND").dt.isoformat()
                    if component.get("DTEND")
                    else None
                ),
                "description": str(component.get("DESCRIPTION")),
            }
            rrule = component.get("RRULE")
            if rrule:
                rrule_str = rrule.to_ical().decode("utf-8")
                rule = rrulestr(rrule_str, dtstart=component.get("DTSTART").dt)
                for dt in rule:
                    event_data = {
                        "title": str(component.get("SUMMARY")),
                        "start": dt.isoformat(),
                        "end": (
                            (
                                dt
                                + (
                                    component.get("DTEND").dt
                                    - component.get("DTSTART").dt
                                )
                            ).isoformat()
                            if component.get("DTEND")
                            else None
                        ),
                        "description": str(component.get("DESCRIPTION")),
                    }
                    events.append(event_data)
            else:
                events.append(event_data)

    return HttpResponse(dumps(events))
