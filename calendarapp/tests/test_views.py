from django.test import TestCase
from django.contrib.auth import get_user_model

from calendarapp.views import upload_calendar, parse_ics, prep_events, update_event, delete_calendar

CustomUser = get_user_model()

class UploadCalendarViewTest(TestCase):
    def setUp(self):
            self.user = CustomUser.objects.create_user(
                username='testuser',
                password='testpass123'
            )