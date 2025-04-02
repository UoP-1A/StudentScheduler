from django.urls import path
from study_sessions import views
from .views import get_sessions, create, create_recurring

app_name = 'study_sessions'

urlpatterns = [
    path('create/', create, name='create'),
    path('create_recurring/<int:session_id>/', create_recurring, name='create_recurring'),
    path('sessions/', get_sessions, name='get_sessions'),
]

