from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils.timezone import now, timedelta
from django.http import JsonResponse

from calendarapp.models import Calendar, Event
from calendarapp.views import prep_events

import json

CustomUser = get_user_model()

class UploadCalendarViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.valid_ics_content = """
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//hacksw/handcal//NONSGML v1.0//EN
BEGIN:VEVENT
UID:uid1@example.com
DTSTAMP:19970714T170000Z
ORGANIZER;CN=John Doe:MAILTO:john.doe@example.com
DTSTART:19970714T170000Z
DTEND:19970715T035959Z
SUMMARY:Bastille Day Party
END:VEVENT
END:VCALENDAR
        """
        self.invalid_file_content = "This is not an ICS file"

    def test_upload_calendar_requires_login(self):
        """
        Test that the view requires authentication
        """
        url = reverse('upload_calendar')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/accounts/login/'))

    def test_rejects_non_ics_files(self):
        """
        Test that non-ICS files are rejected
        """
        self.client.login(username='testuser', password='testpass123')
        
        txt_file = SimpleUploadedFile(
            "test.txt",
            self.valid_ics_content.encode('utf-8'),
            content_type="text/plain"
        )
        
        response = self.client.post(
            reverse('upload_calendar'),
            {'name': 'Test Calendar', 'ics_file': txt_file},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Calendar.objects.filter(name='Test Calendar').exists())
        self.assertContains(response, "File must have .ics extension")

    def test_calendar_assigned_to_correct_user(self):
        """
        Test that calendar is assigned to the requesting user
        """
        self.client.login(username='testuser', password='testpass123')
        
        ics_file = SimpleUploadedFile(
            "test.ics",
            self.valid_ics_content.encode('utf-8'),
            content_type="text/calendar"
        )
        
        self.client.post(
            reverse('upload_calendar'),
            {'name': 'User Calendar', 'ics_file': ics_file},
            format='multipart'
        )
        
        calendar = Calendar.objects.get(name='User Calendar')
        self.assertEqual(calendar.user, self.user)

    def test_invalid_post_returns_form(self):
        """
        Test that invalid POST returns form with 200 status to allow for server validation response
        """
        self.client.login(username='testuser', password='testpass123')
        
        ics_file = SimpleUploadedFile(
            "test.ics",
            self.valid_ics_content.encode('utf-8'),
            content_type="text/calendar"
        )
        
        response = self.client.post(
            reverse('upload_calendar'),
            {'ics_file': ics_file},  # name is missing
            format='multipart'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form')

