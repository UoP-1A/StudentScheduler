from django.urls import path
from study_sessions import views
from .views import get_sessions

app_name = 'study_sessions'

urlpatterns = [
    path('create/', views.CreateStudySessionView.as_view(), name='create_session'),
    path('sessions/', views.get_sessions, name='get_sessions'),
]