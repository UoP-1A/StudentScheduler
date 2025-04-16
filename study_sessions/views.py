from django.shortcuts import render, redirect
from django.views import View
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import StudySession

from .forms import StudySessionForm

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
    context = {
        'form': form
    }
    return render(request, 'study_sessions/create.html', context)


def get_sessions(request):
    sessions = StudySession.objects.all()
    sessions_list = []
    for session in sessions:
        sessions_list.append({
            'id': session.id,
            'title': session.title,
            'description': session.description,
            'start_time': session.start_time,
            'end_time': session.end_time,
            'date': session.date,
            'is_recurring': session.is_recurring,
            'host_id': session.host_id,
            'calendar_id': session.calendar_id_id,
        })
    return JsonResponse(sessions_list, safe=False)