from zoneinfo import ZoneInfo
from datetime import datetime
from django.utils.timezone import make_aware
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from .models import StudySession, RecurringStudySession, StudySessionParticipant
from rest_framework.decorators import api_view
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied

from util.format_datetime import format_datetime
from .forms import StudySessionForm, RecurringSessionForm

@login_required
@csrf_exempt
def create(request):
    form = StudySessionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        study_session = form.save(commit=False)
        study_session.host = request.user
        study_session.save()
        
        # Explicitly save participants if needed
        participants = form.cleaned_data.get('participants', [])
        for participant in participants:
            StudySessionParticipant.objects.get_or_create(
                study_session=study_session,
                participant=participant
            )
        
        if study_session.is_recurring:
            return redirect('create_recurring', session_id=study_session.id)
        return redirect('./')
    
    return render(request, 'study_sessions/create.html', {'form': form})

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