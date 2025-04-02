from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from .models import Module, Grade
from rest_framework.decorators import api_view

# Create your views here.

def index(request):
    return redirect('/calendar')

@login_required
@api_view(['GET'])
def get_modules(request):
    user = request.user
    modules = user.modules.all()

    return render(request, "modules/modules.html", {"modules": modules})

@login_required
@api_view(['POST'])
def add_module(request):
    pass

@login_required
@api_view(['POST'])
def add_grade(request):
    pass

@login_required
@api_view(['DELETE'])
def delete_module(request):
    pass

@login_required
@api_view(['DELETE'])
def delete_grade(request):
    pass
