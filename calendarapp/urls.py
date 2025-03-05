from django.urls import path

from . import views


urlpatterns = [
    path("", views.index, name="index"),
    path("get-calendar/", views.prep_events, name="prep_events"),
    path("upload-calendar/", views.upload_calendar, name="upload_calendar"),
    path("delete-calendar/<int:calendar_id>/", views.delete_calendar, name="delete_calendar"),
    path('update-event/', views.update_event, name='update_event'),
] 