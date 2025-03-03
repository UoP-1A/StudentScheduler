from django.contrib import admin
from .models import Calendar, Event

# Register your models here.
admin.site.register(Calendar)
admin.site.register(Event)