from zoneinfo import ZoneInfo
from datetime import datetime, timedelta, time
from django.utils.timezone import make_aware
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.test import Client
from .models import StudySession, RecurringStudySession, StudySessionParticipant
from rest_framework.decorators import api_view
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.auth.decorators import login_required
from django.db.models import Q


import requests
from .forms import AutoStudySessionForm, ManualStudySessionForm, RecurringSessionForm
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied

from util.format_datetime import format_datetime
from .forms import StudySessionForm, RecurringSessionForm

@login_required
@csrf_exempt
def method_of_creation(request):
    automated = 0
    return render(request, 'study_sessions/methods.html')

@login_required
@csrf_exempt
def create(request, automated=0):
    if automated == 0:
        form = ManualStudySessionForm
    else:
        form = AutoStudySessionForm
    if request.method == 'POST':
        print(request.POST)
        if automated == 0:
            form = ManualStudySessionForm(request.POST)
        else:
            form = AutoStudySessionForm(request.POST)
        if form.is_valid():
            study_session = form.save(commit=False)
            study_session.host = request.user
            if automated == 1:
                events = []
                #urls = ['study_sessions:get_sessions']
                urls = ['study_sessions:get_sessions', 'prep_events']

                #fetch all events and sessions from the calendar
                for url_name in urls:
                    url = request.build_absolute_uri(reverse(url_name))
                    response = requests.get(url, cookies=request.COOKIES)
                    if response.status_code == 200:
                        data = response.json()
                        for item in data:
                            rrule = str(item.get('rrule'))
                            rrule_count = 0
                            if rrule != "None":
                                rrule_split = rrule.split(';')
                                for rrule_item in rrule_split:
                                    if rrule_item.startswith('COUNT='):
                                        rrule_count = int(rrule_item.split('=')[1])
                                        print("rrule count: ", rrule_count)
                                if rrule_count == 1:
                                    start = datetime.fromisoformat(item.get('start'))
                                    end = datetime.fromisoformat(item.get('end'))
                                    session_data = {
                                        'start': str(start),
                                        'end': str(end),
                                    }
                                    events.append(session_data)
                                    print(session_data, "     ", item.get("type"))
                                else:
                                    for i in range(rrule_count-1):
                                        start = datetime.fromisoformat(item.get('start'))
                                        end = datetime.fromisoformat(item.get('end'))
                                        start = start + timedelta(weeks=i)
                                        end = end + timedelta(weeks=i)
                                        session_data = {
                                            'start': str(start),
                                            'end': str(end),
                                        }
                                        events.append(session_data)
                                        print(session_data, "     ", item.get("type"))
                            else:
                                start = datetime.fromisoformat(item.get('start'))
                                end = datetime.fromisoformat(item.get('end'))
                                session_data = {
                                    'start': str(start),
                                    'end': str(end),
                                }
                                events.append(session_data)
                                print(session_data, "     ", item.get("type"))
                            
                #filter out events that aren't between now and the end of the week
                #today = make_aware(datetime.combine(datetime.now().replace(day=7).date(), time(10, 0)),timezone=ZoneInfo("UTC"))

                today = make_aware(datetime.now(), timezone=ZoneInfo("UTC"))
                days_left_until_sat = (5 - today.weekday()) % 7
                days_left_until_mon = (0 - today.weekday()) % 7
                if days_left_until_sat == 0:
                    days_left_until_sat = 7
                end_of_week = (today + timedelta(days=days_left_until_sat)).replace(hour=0, minute=0, second=0, microsecond=0)
                if days_left_until_mon == 0:
                    days_left_until_mon = 7
                start_of_week = (today + timedelta(days=days_left_until_mon)).replace(hour=0, minute=0, second=0, microsecond=0)

                print("start of week(", start_of_week, ") end of week(", end_of_week , ") - day now (", today , ") days left until sat:", days_left_until_sat, "days left until mon:", days_left_until_mon)
                events_left_this_week = []
                for event in events:
                    event_start = datetime.fromisoformat(event['start'])
                    if event_start < end_of_week:
                        if (event_start >= today) and (event_start >= start_of_week):
                            events_left_this_week.append(event)

                #create a list of events for each day of the week
                week_of_events = []
                for i in range(days_left_until_mon, days_left_until_sat+1):
                    day_of_events = []
                    for event in events_left_this_week:
                        event_start = datetime.fromisoformat(event['start'])
                        print("day: ", i, " ", event_start, "==", (today + timedelta(days=i)).date())
                        if event_start.date() == (today + timedelta(days=i)).date():
                            day_of_events.append(event)
                    week_of_events.append(day_of_events)

                #find how many hours are used up for each day of the week
                hours_per_day = []
                for day_of_events in week_of_events:
                    hours = 0
                    for event in day_of_events:
                        hours += round((datetime.fromisoformat(event['end']) - datetime.fromisoformat(event['start'])).seconds / 3600)
                    hours_per_day.append(hours)



                #pick a day that has the least amount of hours, while avoiding days with 0 hours so the user can have a free day
                day_of_new_session = 0
                minimum_hours = 8
                for day in hours_per_day:
                    if day == 0 or day >= 8:
                        continue
                    elif day < minimum_hours:
                        minimum_hours = day
                        day_of_new_session = hours_per_day.index(day)
                if minimum_hours == 8:
                    day = 0
                    while day < len(hours_per_day):
                        if hours_per_day[day] == 0:
                            day_of_new_session = day 
                            minimum_hours = 0
                        day += 1
                    if minimum_hours != 0:
                        print("No available day for new session")
                        #should break out of function here ngl
                        
                #if all days have 0 hours, pick the next day at noon
                day_of_events = week_of_events[day_of_new_session]
                if len(day_of_events) == 0:
                    print("No events for this day")
                    auto_date = today + timedelta(days=1)
                    auto_date = auto_date.replace(hour=12, minute=0, second=0, microsecond=0)
                    study_session.date = auto_date.date()
                    study_session.start_time = auto_date.strftime("%H:%M:%S")
                    study_session.end_time = (auto_date + timedelta(hours=2)).strftime("%H:%M:%S")
                else:
                    #find the gaps in between the events throughout the day
                    hours_between_each_event = []
                    for i in range(len(day_of_events)):
                        if i != 0:
                            hours = datetime.fromisoformat(day_of_events[i]['start']) - datetime.fromisoformat(day_of_events[i-1]['end'])
                            hours_between_each_event.append(hours)

                    duration = 1
                    timezone_offset = -1 # this is a placeholder, the calendar is being weird
                    auto_date = datetime.now()

                    #find a decent gap between the events to put the new session in
                    session_created = False
                    for hour in hours_between_each_event:
                        hour_index = hours_between_each_event.index(hour)
                        if hour == timedelta(hours=2):
                            #if there is a 2 hour gap, put the session at the start and leave the user a 1 hour break
                            print("session created for 1 hour")
                            session_created = True
                            auto_date = datetime.fromisoformat(day_of_events[hour_index]['end'])
                            duration = 1
                        elif hour == timedelta(hours=3):
                            #if there is a 3 hour gap, put the session next to the event that is shortest and leave an hour break with the other
                            print("session created for 2 hours")
                            session_created = True
                            duration_of_previous = datetime.fromisoformat(day_of_events[hour_index]['end']) - datetime.fromisoformat(day_of_events[hour_index]['start'])
                            duration_of_next = datetime.fromisoformat(day_of_events[hour_index+1]['end']) - datetime.fromisoformat(day_of_events[hour_index+1]['start'])
                            if duration_of_previous <= duration_of_next:
                                auto_date = datetime.fromisoformat(day_of_events[hour_index]['end'])
                                duration = 2
                            else:
                                auto_date = datetime.fromisoformat(day_of_events[hour_index+1]['start']) - timedelta(hours=2+timezone_offset)
                                duration = 2
                        elif hour >= timedelta(hours=4):
                            #if there is a gap of 4+ hrs, put session 1 hour after the end of the last event and have it last 2 hours
                            print("session created for 2 hours")
                            session_created = True
                            auto_date = datetime.fromisoformat(day_of_events[hour_index]['end']) + timedelta(hours=1+timezone_offset)
                            duration = 2

                    #if no gaps were found, create the session either before or after the events
                    if not session_created:
                        before_event = timedelta(9)
                        after_event = timedelta(9)
                        if (datetime.fromisoformat(day_of_events[0]['start']) - datetime.fromisoformat(day_of_events[0]['start']).replace(hour=9, minute=0, second=0, microsecond=0)).total_seconds()/3600 >= 2.0:
                            before_event = datetime.fromisoformat(day_of_events[0]['start']) - datetime.fromisoformat(day_of_events[0]['start']).replace(hour=9, minute=0, second=0, microsecond=0)
                        if (datetime.fromisoformat(day_of_events[-1]['end']).replace(hour=18, minute=0, second=0, microsecond=0) - datetime.fromisoformat(day_of_events[-1]['end'])).total_seconds()/3600 >= 2.0:
                            after_event = datetime.fromisoformat(day_of_events[-1]['end']).replace(hour=18, minute=0, second=0, microsecond=0) - datetime.fromisoformat(day_of_events[-1]['end'])

                        #put session either before or after depending on which gap is bigger
                        if before_event > after_event:
                            before_event = timedelta(hours=9) - before_event
                            if before_event == timedelta(hours=2):
                                print("session created before event ")
                                session_created = True
                                auto_date = datetime.fromisoformat(day_of_events[0]['start']) - timedelta(hours=2+timezone_offset)
                                duration = 1
                            else:
                                print("session created before event ")
                                session_created = True
                                print("start of event: ", day_of_events[0]['start'])
                                auto_date = datetime.fromisoformat(day_of_events[0]['start']) - timedelta(hours=3+timezone_offset)
                                print("auto date: ", auto_date)
                                duration = 2
                        elif after_event > before_event:
                            after_event = timedelta(hours=9) - after_event
                            if after_event == timedelta(hours=2):
                                print("session created after event ")
                                session_created = True
                                auto_date = datetime.fromisoformat(day_of_events[-1]['end']) + timedelta(hours=1+timezone_offset)
                                duration = 1
                            else:
                                print("session created after event ")
                                session_created = True
                                auto_date = datetime.fromisoformat(day_of_events[-1]['end']) + timedelta(hours=1+timezone_offset)
                                duration = 2

                    study_session.date = auto_date.date()
                    study_session.start_time = auto_date.strftime("%H:%M:%S")
                    study_session.end_time = (auto_date + timedelta(hours=duration)).strftime("%H:%M:%S")
            study_session.save()

            participants = form.cleaned_data['participants']
            for participant in participants:
                StudySessionParticipant.objects.create(study_session=study_session, participant=participant)

            if study_session.is_recurring:
                session_id = study_session.id
                return redirect('study_sessions:create_recurring', session_id)
            else:
                return redirect('./')
    context = {
        'form': form
    }
    return render(request, 'study_sessions/create.html', context)

@login_required
def create_recurring(request, session_id):
    # Get session or return 404
    session = get_object_or_404(StudySession, id=session_id)
    
    # Verify permissions
    if session.host != request.user:
        raise PermissionDenied
        
    # Verify session is marked as recurring
    if not session.is_recurring:
        return HttpResponseBadRequest("Session must be marked as recurring")

    if request.method == 'POST':
        form = RecurringSessionForm(request.POST)
        if form.is_valid():
            recurring_session = form.save(commit=False)
            recurring_session.session_id = session
            recurring_session.save()
            return redirect('index')
    else:
        form = RecurringSessionForm()

    return render(request, 'study_sessions/create_recurring.html', {
        'form': form,
        'session': session
    })

@login_required
@api_view(['GET'])
def get_sessions(request):
    user = request.user

    sessions = StudySession.objects.filter(Q(host=user) | Q(participants_set__participant=user))
    sessions = sessions.distinct()
    sessions_list = []
    for session in sessions:
        start_datetime = make_aware(datetime.combine(session.date, session.start_time), timezone=ZoneInfo("UTC"))
        end_datetime = make_aware(datetime.combine(session.date, session.end_time), timezone=ZoneInfo("UTC"))

        duration = str(end_datetime - start_datetime)

        new_session = {
            'id': session.id,
            'title': session.title,
            'type': 'study',
            'start': start_datetime.isoformat(),
            'end':  end_datetime.isoformat(),
            'description': session.description,
            "model": "StudySession",
            #'is_recurring': session.is_recurring,
            #'host_id': session.host_id,
            #'participants': [participant.id for participant in session.participants.all()],
            #'calendar_id': session.calendar_id_id,
        }

        if session.is_recurring:
            recurring_session = RecurringStudySession.objects.filter(session_id=session.id).first()
            if recurring_session:
                count = recurring_session.recurrence_amount
                rrule_dt_str = format_datetime(start_datetime)
                day = session.date.strftime('%A')[:2].upper()
                new_session["rrule"] = ("DTSTART:" + rrule_dt_str + "\n" + "RRULE:FREQ=WEEKLY;BYDAY=" + day + ";COUNT=" + str(count))
        else:
            day = session.date.strftime('%A')[:2].upper()
            rrule_dt_str = format_datetime(start_datetime)
            new_session["rrule"] = ("DTSTART:" + rrule_dt_str + "\n" + "RRULE:FREQ=WEEKLY;BYDAY=" + day + ";COUNT=1")
        new_session["duration"] = duration

        sessions_list.append(new_session)

    return JsonResponse(sessions_list, safe=False, encoder=DjangoJSONEncoder)

@login_required
def get_recurring_sessions(request):
    sessions = RecurringStudySession.objects.all()
    sessions_list = []
    for session in sessions:
        sessions_list.append({
            'id': session.id,
            'recurrence_amount': session.recurrence_amount,
            'session_id': session.session_id.id,
        })
    return JsonResponse(sessions_list, safe=False)

