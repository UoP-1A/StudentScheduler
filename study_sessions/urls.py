from django.urls import path
from study_sessions import views

app_name = 'study_sessions'

urlpatterns = [
    path('create/', views.CreateStudySessionView.as_view(), name='create_session'),
]