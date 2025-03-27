from django import forms
from .models import StudySession
from users.models import CustomUser
from calendarapp.models import Calendar

class StudySessionForm(forms.ModelForm):
    #participants = forms.ModelMultipleChoiceField(queryset=CustomUser.objects.none(),widget=forms.SelectMultiple(attrs={'class': 'form-control'}),required=False)

    class Meta:
        model = StudySession
        fields = '__all__'

