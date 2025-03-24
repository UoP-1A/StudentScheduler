from django.urls import path
from study_sessions import views
from .views import get_sessions, create

app_name = 'study_sessions'

urlpatterns = [
    path('create/', create, name='create'),
    path('sessions/', get_sessions, name='get_sessions'),
]

