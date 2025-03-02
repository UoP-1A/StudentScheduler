from django import forms
from .models import StudySession
from users.models import CustomUser

class StudySessionForm(forms.ModelForm):
    participants = forms.ModelMultipleChoiceField(
        queryset=CustomUser.objects.none(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
        required=False
    )

    class Meta:
        model = StudySession
        fields = ['participants', 'title', 'description', 'start_time', 'end_time', 'date', 'is_recurring']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Title'}),
            'description': forms.Textarea(attrs={'placeholder': 'Description'}),
            'start_time': forms.DateTimeInput(attrs={'placeholder': 'Start Time', 'type': 'time'}),
            'end_time': forms.DateTimeInput(attrs={'placeholder': 'End Time', 'type': 'time'}),
            'date': forms.DateInput(attrs={'placeholder': 'Date', 'type': 'date'}),
            'is_recurring': forms.CheckboxInput(attrs={'placeholder': 'Recurring'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #Temporary friend list: will be replaced with user's friends
        self.fields['participants'].choices = [
            ('1', 'User 1'),
            ('2', 'User 2'),
            ('3', 'User 3'),
            ('4', 'User 4'),
            ('5', 'User 5'),
        ]