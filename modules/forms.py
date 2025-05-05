from django import forms

from .models import Module

class ModuleCreateForm(forms.Form):
    name = forms.CharField(
        max_length=255,
        widget=forms.TextInput()
    )
    credits = forms.IntegerField(
        min_value=0,
        widget=forms.NumberInput(),
    )

class GradeCreateForm(forms.Form):
    module = forms.ModelChoiceField(
        queryset=Module.objects.all(),
        empty_label="Select a module",
        widget=forms.Select()
    )
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput()
    )
    mark = forms.FloatField(
        min_value=0.00,
        max_value=100.00,
        widget=forms.NumberInput()
    )
    weight = forms.IntegerField(
        min_value=0.00,
        max_value=100.00,
        widget=forms.NumberInput()
    )