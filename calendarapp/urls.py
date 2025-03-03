from django.urls import path

from .views import index, prep_events, upload_calendar, delete_calendar


urlpatterns = [
    path("", index, name="index"),
    path("get-calendar/", prep_events, name="prep_events"),
    path("upload-calendar/", upload_calendar, name="upload_calendar"),
    path("delete-calendar/<int:calendar_id>/", delete_calendar, name="delete_calendar")
] 