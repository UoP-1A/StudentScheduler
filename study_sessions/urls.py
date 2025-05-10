from django.urls import path, include
from .views import get_sessions, create, create_recurring, get_recurring_sessions, method_of_creation

app_name = 'study_sessions'

urlpatterns = [
    path('methods/', method_of_creation, name='methods'),
    path('create/<int:automated>/', create, name='create'),
    path('create_recurring/<int:session_id>/', create_recurring, name='create_recurring'),
    path('sessions/', get_sessions, name='get_sessions'),
    path('recurring_sessions/', get_recurring_sessions, name='get_recurring_sessions'),
]

