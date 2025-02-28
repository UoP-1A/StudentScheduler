from django.urls import path

from .views import index, prep_events, upload_calendar, delete_calendar
from . import views


urlpatterns = [
    path("", index, name="index"),
    path("api/get-calendar/", prep_events, name="prep_events"),
    path("upload-calendar/", upload_calendar, name="upload_calendar"),
    path("delete-calendar/<int:calendar_id>/", delete_calendar, name="delete_calendar")
] 

urlpatterns = [
    path('create/', views.create_event, name='create_event'),
    path('edit/<int:event_id>/', views.edit_event, name='edit_event'),
    path('delete/<int:event_id>/', views.delete_event, name='delete_event'),
]