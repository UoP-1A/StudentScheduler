from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError

from rest_framework.decorators import api_view

from .forms import ModuleCreateForm, GradeCreateForm
from .models import Module, Grade

# Create your views here.

def index(request):
    return redirect('/modules')

@login_required
@api_view(['GET'])
def get_modules(request):
    user = request.user
    modules = user.modules.all()
    module_form = ModuleCreateForm()
    grade_form = GradeCreateForm()

    return render(request, "modules/modules.html", {
        "modules": modules,
        "module_form": module_form,
        "grade_form": grade_form,
    })

@login_required
@api_view(['POST'])
def add_module(request):
    module_form = ModuleCreateForm(request.POST)
    if module_form.is_valid():
        try:
            Module.objects.create(
                user=request.user,
                name=module_form.cleaned_data['name'], 
                credits=module_form.cleaned_data['credits'],
            )
        except ValidationError as e:
            module_form.add_error(None, e.message)
            messages.error(request, "Failed to add module: " + str(e))
            return render(request, 'modules/modules.html', {'module_form': module_form})
        
        return redirect("/modules")

@login_required
@api_view(['POST'])
def add_grade(request):
    grade_form = GradeCreateForm(request.POST)
    if grade_form.is_valid():
        try:
            Grade.objects.create(
                module=grade_form.cleaned_data['module'],
                name=grade_form.cleaned_data['name'],
                mark=grade_form.cleaned_data['mark'],
                weight=grade_form.cleaned_data['weight'],
            )
        except ValidationError as e:
            grade_form.add_error(None, e.message)
            messages.error(request, "Failed to add grade: " + str(e))
            return render(request, 'modules/modules.html', {'grade_form': grade_form})
        
        return redirect("/modules")

@login_required
@api_view(['POST'])
def delete_module(request, module_id):
    module = get_object_or_404(Module, id=module_id, user=request.user)

    module.delete()
    messages.success(request, "Module deleted successfully.")

    return redirect("/modules")

@login_required
@api_view(['POST'])
def delete_grade(request, grade_id):
    grade = get_object_or_404(Grade, id=grade_id)

    grade.delete()
    messages.success(request, "Grade deleted successfully.")

    return redirect("/modules")
