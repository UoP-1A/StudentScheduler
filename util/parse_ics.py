from calendarapp.models import Event
from dateutil.rrule import rrulestr
from icalendar import Calendar as ICalCalendar

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