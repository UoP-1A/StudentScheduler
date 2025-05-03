from zoneinfo import ZoneInfo
from datetime import datetime, timedelta
from django.utils.timezone import make_aware
from django.shortcuts import render, redirect
from django.views import View
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import StudySession, RecurringStudySession, StudySessionParticipant
from rest_framework.decorators import api_view
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from .forms import StudySessionForm, RecurringSessionForm

from dateutil.rrule import rrulestr

@login_required
@csrf_exempt
def create(request):
    form = StudySessionForm()
    if request.method == 'POST':
        print(request.POST)
        form = StudySessionForm(request.POST)
        if form.is_valid():
            study_session = form.save(commit=False)
            study_session.host = request.user
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

def create_recurring(request, session_id):
    session = StudySession.objects.get(id=session_id)
    form = RecurringSessionForm()
    if request.method == 'POST':
        form = RecurringSessionForm(request.POST)
        if form.is_valid():
            recurring_session = form.save(commit=False)
            recurring_session.session_id = session
            recurring_session.save()
            return redirect('index')
    context = {
        'form': form
    }
    return render(request, 'study_sessions/create_recurring.html', context)

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

def format_datetime(start_datetime):
    year = str(start_datetime.year)
    month = start_datetime.month
    day_of_month = start_datetime.day
    if month < 10:
        month_string = "0" + str(month)
    else:
        month_string = str(month)
    if day_of_month < 10:
        day_of_month_as_string = "0" + str(day_of_month)
    else:
        day_of_month_as_string = str(day_of_month)
    
    hour = start_datetime.hour
    minute = start_datetime.minute
    second = start_datetime.second
    if hour < 10:
        hour_as_string = "0" + str(hour)
    else:
        hour_as_string = str(hour)
    if minute < 10:
        minute_as_string = "0" + str(minute)
    else:
        minute_as_string = str(minute)
    if second < 10:
        second_as_string = "0" + str(second)
    else:
        second_as_string = str(second)

    return year + month_string + day_of_month_as_string + "T" + hour_as_string + minute_as_string + second_as_string + "\n"

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