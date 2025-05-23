import json

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.dateparse import parse_datetime
from django.core.exceptions import ValidationError
from django.utils.timezone import datetime
from django.db.models import Q

from .forms import CalendarUploadForm
from .models import Calendar, Event

from study_sessions.models import StudySession, RecurringStudySession

from util.parse_ics import parse_ics

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from dateutil.rrule import rrulestr
from datetime import timedelta

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

@login_required
@api_view(['GET', 'POST'])  # Add POST to allowed methods
def prep_events(request):
    if request.method == 'GET':
        """Handle GET requests (existing code)"""
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
                "model": "Event",
            }
            if e.rrule:
                event_data["rrule"] = e.rrule
            if e.end:
                event_data["duration"] = str(e.duration) if e.duration else None
            event_list.append(event_data)
        return JsonResponse(event_list, safe=False, encoder=DjangoJSONEncoder)
    
    elif request.method == 'POST':
        """Handle POST requests to create new events"""
        try:
            # Validate required fields
            required_fields = ['title', 'start', 'calendar']
            for field in required_fields:
                if field not in request.data:
                    return JsonResponse(
                        {'status': 'error', 'message': f'Missing required field: {field}'},
                        status=400
                    )
            
            # Get calendar and verify ownership
            calendar_id = request.data['calendar']
            try:
                calendar = Calendar.objects.get(id=calendar_id, user=request.user)
            except Calendar.DoesNotExist:
                return JsonResponse(
                    {'status': 'error', 'message': 'Calendar not found or access denied'},
                    status=404
                )
            
            # Create and validate event
            event = Event(
                calendar=calendar,
                title=request.data['title'],
                start=request.data['start'],
                end=request.data.get('end'),
                rrule=request.data.get('rrule'),
                type=request.data.get('type', 'event'),
                description=request.data.get('description', '')
            )
            
            # This will trigger your model's clean() method
            event.full_clean()
            event.save()
            
            return JsonResponse(
                {'status': 'success', 'event_id': event.id},
                status=201
            )
            
        except ValidationError as e:
            return JsonResponse(
                {'status': 'error', 'errors': dict(e)},
                status=400
            )
        except Exception as e:
            return JsonResponse(
                {'status': 'error', 'message': str(e)},
                status=400
            )


@api_view(['POST'])
@login_required
def update_event(request):
    event_id = request.data.get('id')
    start_str = request.data.get('start')
    end_str = request.data.get('end')
    model_type = request.data.get('model')
    
    # Validate required fields
    if not event_id or not start_str or not model_type:
        return Response(
            {'status': 'error', 'message': 'Missing required fields'}, 
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Parse datetimes
        new_start = parse_datetime(start_str)
        if not new_start:
            return Response(
                {'status': 'error', 'message': 'Invalid start datetime format'},
                status=status.HTTP_400_BAD_REQUEST
            )

        new_end = parse_datetime(end_str) if end_str else None

        if model_type.lower() == 'event':
            event = Event.objects.get(id=event_id)
            if event.calendar.user != request.user:
                return Response(
                    {'status': 'error', 'message': 'Permission denied'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Store original duration
            original_duration = event.duration if event.duration else (event.end - event.start if event.end else None)
            
            # Update start time
            event.start = new_start
            
            # Handle end time
            if new_end is not None:
                event.end = new_end
                event.duration = None  # Let model recalculate
            elif original_duration:  # Maintain duration
                event.end = new_start + original_duration
                event.duration = original_duration
            
            try:
                event.full_clean()
                event.save()
            except ValidationError as e:
                return Response(
                    {'status': 'error', 'message': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
        elif model_type.lower() == 'studysession':
            # Similar logic for StudySession
            study_session = StudySession.objects.get(id=event_id)
            if study_session.host != request.user:
                return Response(
                    {'status': 'error', 'message': 'Permission denied'},
                    status=status.HTTP_403_FORBIDDEN
                )
            

            original_start = study_session.start_time
            original_end = study_session.end_time
            
            study_session.start_time = new_start
            if new_end is not None:
                study_session.end_time = new_end
            elif original_end:
                duration = original_end - original_start
                study_session.end_time = new_start + duration
            
            if study_session.end_time and study_session.start_time and study_session.end_time <= study_session.start_time:
                return Response(
                    {'status': 'error', 'message': f'End time must be after start time'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            study_session.save()
            
        else:
            return Response(
                {'status': 'error', 'message': 'Invalid model type'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response({
            'status': 'success',
            'event_id': event_id,
            'new_start': new_start,
            'new_end': new_end if new_end else (event.end if model_type.lower() == 'event' else study_session.end_time),
            'model': model_type
        })

    except (Event.DoesNotExist, StudySession.DoesNotExist):
        return Response(
            {'status': 'error', 'message': 'Event not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'status': 'error', 'message': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )

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

@login_required
def search_results(request):
    query = request.GET.get('q')
    recurring_events = []
    single_events = []
    session_results = []
    recurring_sessions = []

    if query:
        # Search for recurring events
        now_time = datetime.now() - timedelta(days=365)
        oneYear = datetime.now() + timedelta(days=365)

        for event in Event.objects.exclude(rrule=None):
            rule = rrulestr(event.rrule, dtstart=event.start)
            occurrences = list(rule.between(now_time, oneYear, inc=True))

            for occurrence in occurrences:
                if query.lower() in event.title.lower() or query.lower() in event.description.lower() or query.lower() in str(occurrence).lower():
                    recurring_events.append({
                        'id': event.id,
                        'title': event.title,
                        'start': occurrence,
                        'end': occurrence + (event.end - event.start),
                        'description': event.description
                    })

        # Search for single events
        single_events = Event.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(start__icontains=query),
            rrule=None
        ).values('id', 'title', 'start', 'end', 'description')

        recurring_events = sorted(recurring_events, key=lambda x: x['start'], reverse=True)
        single_events = sorted(single_events, key=lambda x: x['start'], reverse=True)

        # Rest of your code for sessions...
        recurring_sessions = [] 

        for recurring_session in RecurringStudySession.objects.select_related('session_id'):
            session = recurring_session.session_id
            if query.lower() in session.title.lower():
                rule = rrulestr(
                    f"FREQ=WEEKLY;COUNT={recurring_session.recurrence_amount}",
                    dtstart=datetime.combine(session.date, session.start_time)
                )
                occurrences = list(rule)

                for occurrence in occurrences:
                        recurring_sessions.append({
                            'id': session.id,
                            'title': session.title,
                            'start_time': occurrence,
                            'end_time': occurrence + (datetime.combine(session.date, session.end_time) - datetime.combine(session.date, session.start_time)),
                            'description': session.description,
                            'host': session.host  
                        })

        recurring_sessions = sorted(recurring_sessions, key=lambda x: x['start_time'], reverse=True)

        session_results = StudySession.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        ).distinct().order_by('start_time')

    combined_results = {
        'query': query,
        'event_results': list(recurring_events) + list(single_events),
        'session_results': list(recurring_sessions) + list(session_results),
        'event_results_count': len(recurring_events) + len(single_events),
        'session_results_count': len(recurring_sessions) + len(session_results)
    }

    return render(request, 'search_results.html', combined_results)