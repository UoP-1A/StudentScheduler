from django.contrib import admin
from .models import Calendar, CalendarEvent

# Register your models here.
admin.site.register(Calendar)
admin.site.register(CalendarEvent)