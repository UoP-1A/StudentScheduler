from django.shortcuts import render, redirect
from django.views import View
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import StudySession

from .forms import StudySessionForm

@csrf_exempt
def create(request):
    form = StudySessionForm()
    if request.method == 'POST':
        print(request.POST)
        form = StudySessionForm(request.POST)
        if form.is_valid():
            form.save()
    context = {
        'form': form
    }
    return render(request, 'study_sessions/create.html', context)


def get_sessions(request):
    sessions = StudySession.objects.all()
    context = {
        'sessions': sessions
    }
    return render(request, 'study_sessions/sessions.html', context)