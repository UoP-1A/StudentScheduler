from zoneinfo import ZoneInfo
from datetime import datetime, timedelta
from django.utils.timezone import make_aware
from django.shortcuts import render, redirect
from django.views import View
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import StudySession, RecurringStudySession
from rest_framework.decorators import api_view
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.auth.decorators import login_required
from .models import StudySession

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
    sessions = StudySession.objects.all()
    sessions_list = []
    for session in sessions:
        start_datetime = make_aware(datetime.combine(session.date, session.start_time), timezone=ZoneInfo("UTC"))
        end_datetime = make_aware(datetime.combine(session.date, session.end_time), timezone=ZoneInfo("UTC"))

        duration = str(end_datetime - start_datetime)

        new_session = {
            'id': session.id,
            'title': session.title,
            'start': start_datetime.isoformat(),
            'end':  end_datetime.isoformat(),
            'description': session.description,
            #'is_recurring': session.is_recurring,
            #'host_id': session.host_id,
            #'calendar_id': session.calendar_id_id,
        }

        if session.is_recurring:
            recurring_session = RecurringStudySession.objects.filter(session_id=session.id).first()
            if recurring_session:
                count = recurring_session.recurrence_amount
                day = session.date.strftime('%A')[:2].upper()
                new_session["rrule"] = ("FREQ=WEEKLY;BYDAY=" + day + ";COUNT=" + str(count))
        new_session["duration"] = duration

        sessions_list.append(new_session)

    return JsonResponse(sessions_list, safe=False, encoder=DjangoJSONEncoder)

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