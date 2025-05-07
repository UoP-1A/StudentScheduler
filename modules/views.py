from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError

from rest_framework.decorators import api_view

from .forms import ModuleCreateForm, GradeCreateForm
from .models import Module, Grade

# Create your views here.

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
    if request.method == 'POST':
        module_form = ModuleCreateForm(request.POST)
        if module_form.is_valid():
            try:
                Module.objects.create(
                    user=request.user,
                    name=module_form.cleaned_data['name'], 
                    credits=module_form.cleaned_data['credits'],
                )
                messages.success(request, "Module added successfully")
                return redirect("/modules")
            except ValidationError as e:
                module_form.add_error(None, e)
                messages.error(request, f"Failed to add module: {e}")
        
        # Return the form with errors for invalid submissions
        return render(request, 'modules/modules.html', {
            'module_form': module_form,
            'grade_form': GradeCreateForm()  # Make sure to include all required forms
        })
    
    # Handle GET requests if needed
    return redirect("/modules")

@login_required
@api_view(['POST'])
def add_grade(request):
    if request.method == 'POST':
        grade_form = GradeCreateForm(request.POST)
        if grade_form.is_valid():
            try:
                Grade.objects.create(
                    module=grade_form.cleaned_data['module'],
                    name=grade_form.cleaned_data['name'],
                    mark=grade_form.cleaned_data['mark'],
                    weight=grade_form.cleaned_data['weight'],
                )
                messages.success(request, "Grade added successfully")
                return redirect("/modules")
            except ValidationError as e:
                messages.error(request, f"Failed to add grade: {e}")
                return render(request, 'modules/modules.html', {
                    'grade_form': grade_form,
                    'module_form': ModuleCreateForm(),
                    'modules': request.user.modules.all()
                })
        
        # Return with form errors for invalid submissions
        return render(request, 'modules/modules.html', {
            'grade_form': grade_form,
            'module_form': ModuleCreateForm(),
            'modules': request.user.modules.all()
        })
    
    return redirect("/modules")

@login_required
@api_view(['POST'])
@require_http_methods(["POST"])  # Only allow POST requests
def delete_module(request, module_id):
    module = get_object_or_404(Module, id=module_id, user=request.user)
    
    if request.method == 'POST':
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
