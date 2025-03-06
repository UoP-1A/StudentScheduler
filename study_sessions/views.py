from django.shortcuts import render, redirect
from django.views import View
from django.http import JsonResponse
from .models import StudySession

from .forms import StudySessionForm

class CreateStudySessionView(View):
    form_class = StudySessionForm
    initial = {"key": "value"}
    template_name = "study_sessions/create.html"

    def get(self, request, *args, **kwargs):
        form = self.form_class(initial=self.initial)
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            form.save()

            return redirect(to="/")
        
        return render(request, self.template_name, {"form": form})
    
def get_sessions(request):
    sessions = StudySession.objects.all().values()
    return JsonResponse(list(sessions), safe=False)

