from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.contrib import messages

from .forms import CalendarUploadForm
from .models import Calendar

from rest_framework.decorators import api_view

from icalendar import Calendar as ICalCalendar
from json import dumps

from common.util import preprocess_ics, processRrule


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
            return redirect(to="/")
    else:
        form = CalendarUploadForm
    return render(request, "calendarapp/upload_calendar.html", {"form": form})

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
