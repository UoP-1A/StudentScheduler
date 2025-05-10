from django import forms
from .models import StudySession, RecurringStudySession
from users.models import CustomUser

class StudySessionForm(forms.ModelForm):
    participants = forms.ModelMultipleChoiceField(
        queryset=CustomUser.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Participants"
    )

    class Meta:
        model = StudySession
        fields = ['participants','title', 'description', 'start_time', 'end_time', 'date', 'is_recurring', 'calendar_id']
        exclude = ['host']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }

class RecurringSessionForm(forms.ModelForm):
    recurrence_amount = forms.IntegerField(
        min_value=1,
        required=True,
        widget=forms.NumberInput(attrs={
            'min': '1',
            'class': 'form-control'
        }),
        error_messages={
            'min_value': 'Recurrence amount must be at least 1',
            'required': 'Recurrence amount is required',
            'invalid': 'Please enter a valid number'
        }
    )

    class Meta:
        model = RecurringStudySession
        fields = ['recurrence_amount']

    def clean_recurrence_amount(self):
        amount = self.cleaned_data.get('recurrence_amount')
        
        # Explicit None check
        if amount is None:
            raise forms.ValidationError("Recurrence amount is required")
            
        # Convert to int if it's a string
        try:
            amount = int(amount)
        except (ValueError, TypeError):
            raise forms.ValidationError("Please enter a valid number")
            
        # Validate minimum value
        if amount < 1:
            raise forms.ValidationError("Recurrence amount must be at least 1")
            
        return amount