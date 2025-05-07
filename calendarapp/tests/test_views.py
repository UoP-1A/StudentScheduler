import json

from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone

from datetime import timedelta

from calendarapp.models import Calendar, Event

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

class PrepEventsViewTests(TestCase):
    def setUp(self):
        """Set up test data before each test method runs."""
        # Create a test user
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpassword'
        )
        
        # Create a calendar for the test user
        self.calendar = Calendar.objects.create(
            user=self.user,
            name='Test Calendar'
        )
        
        # Create test events
        self.now = timezone.now()
        
        # Regular event (no recurrence)
        self.event1 = Event.objects.create(
            calendar=self.calendar,
            title='Regular Event',
            type='event',
            start=self.now,
            end=self.now + timedelta(hours=1),
            description='Regular event description'
        )
        
        # Event with rrule (recurring)
        self.event2 = Event.objects.create(
            calendar=self.calendar,
            title='Recurring Event',
            type='study',
            start=self.now + timedelta(days=1),
            end=self.now + timedelta(days=1, hours=2),
            description='Recurring event description',
            rrule='FREQ=WEEKLY;COUNT=5'
        )
        
        # Event with no end time
        self.event3 = Event.objects.create(
            calendar=self.calendar,
            title='All-day Event',
            type='event',
            start=self.now + timedelta(days=2),
            end=None,
            description='All-day event description'
        )
    
    def test_login_required(self):
        """Test that the view requires login."""
        url = reverse('prep_events')  # Make sure this matches your URL name
        response = self.client.get(url)
        # Should redirect to login page for unauthenticated requests
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/accounts/login/'))
    
    def test_successful_retrieval(self):
        """Test that authenticated users can retrieve their events."""
        self.client.login(username='testuser', password='testpassword')
        url = reverse('prep_events')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        events = json.loads(response.content)
        self.assertEqual(len(events), 3)
        
        event_ids = [e['id'] for e in events]
        self.assertIn(self.event1.id, event_ids)
        self.assertIn(self.event2.id, event_ids)
        self.assertIn(self.event3.id, event_ids)
    
    def test_event_fields(self):
        """Test that all required fields are present in the response."""
        self.client.login(username='testuser', password='testpassword')
        url = reverse('prep_events')
        response = self.client.get(url)
        events = json.loads(response.content)
        
        event1_data = next((e for e in events if e['id'] == self.event1.id), None)
        self.assertIsNotNone(event1_data)
        
        self.assertEqual(event1_data['title'], self.event1.title)
        self.assertEqual(event1_data['type'], self.event1.type)
        self.assertEqual(event1_data['start'], self.event1.start.isoformat())
        self.assertEqual(event1_data['end'], self.event1.end.isoformat())
        self.assertEqual(event1_data['description'], self.event1.description)
        self.assertNotIn('rrule', event1_data)
    
    def test_recurring_event(self):
        """Test that recurring events have the rrule field."""
        self.client.login(username='testuser', password='testpassword')
        url = reverse('prep_events')
        response = self.client.get(url)
        events = json.loads(response.content)
        
        event2_data = next((e for e in events if e['id'] == self.event2.id), None)
        self.assertIsNotNone(event2_data)
        self.assertIn('rrule', event2_data)
        self.assertEqual(event2_data['rrule'], self.event2.rrule)
    
    def test_event_with_no_end(self):
        """Test that events with no end time are handled correctly."""
        self.client.login(username='testuser', password='testpassword')
        url = reverse('prep_events')
        response = self.client.get(url)
        events = json.loads(response.content)
        
        event3_data = next((e for e in events if e['id'] == self.event3.id), None)
        self.assertIsNotNone(event3_data)
        self.assertIsNone(event3_data['end'])
        self.assertNotIn('duration', event3_data)
    
    def test_user_sees_only_own_events(self):
        """Test that users only see events from their calendars."""
        # Create another user with their own calendar and event
        other_user = CustomUser.objects.create_user(
            username='otheruser',
            password='otherpassword'
        )
        
        other_calendar = Calendar.objects.create(
            user=other_user,
            name='Other Calendar'
        )
        
        other_event = Event.objects.create(
            calendar=other_calendar,
            title='Other User Event',
            type='event',
            start=self.now,
            end=self.now + timedelta(hours=1)
        )
        
        # Test with our original user
        self.client.login(username='testuser', password='testpassword')
        url = reverse('prep_events')
        response = self.client.get(url)
        events = json.loads(response.content)
        self.assertEqual(len(events), 3)
        event_ids = [e['id'] for e in events]
        self.assertNotIn(other_event.id, event_ids)
        
        # Test with other user
        self.client.login(username='otheruser', password='otherpassword')
        response = self.client.get(url)
        events = json.loads(response.content)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['id'], other_event.id)
    
    def test_duration_field(self):
        """Test that duration field is included for events with end times."""
        self.event2.duration = timedelta(hours=2)
        self.event2.save()
        
        self.client.login(username='testuser', password='testpassword')
        url = reverse('prep_events')
        response = self.client.get(url)
        events = json.loads(response.content)
        
        event2_data = next((e for e in events if e['id'] == self.event2.id), None)
        self.assertIsNotNone(event2_data)
        self.assertIn('duration', event2_data)
        self.assertEqual(event2_data['duration'], str(self.event2.duration))

    def test_invalid_event_times(self):
        """Test that end time cannot be before start time."""
        self.client.login(username='testuser', password='testpassword')
        invalid_data = {
            'title': 'Invalid Event',
            'start': (self.now + timedelta(hours=1)).isoformat(),
            'end': self.now.isoformat(),  # End before start
            'calendar': self.calendar.id,
            'type': 'event'
        }
        response = self.client.post(
            reverse('prep_events'), 
            data=json.dumps(invalid_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('End time must be after the start time', response.json()['errors']['__all__'][0])

    def test_missing_required_fields(self):
        """Test that required fields are enforced."""
        self.client.login(username='testuser', password='testpassword')
        invalid_data = {
            # Missing 'title' which is required
            'start': self.now.isoformat(),
            'calendar': self.calendar.id,
            'type': 'event'
        }
        response = self.client.post(
            reverse('prep_events'),
            data=json.dumps(invalid_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('Missing required field: title', response.json()['message'])

    def test_nonexistent_calendar(self):
        """Test handling of non-existent calendar IDs."""
        self.client.login(username='testuser', password='testpassword')
        invalid_data = {
            'title': 'Invalid Calendar Event',
            'start': self.now.isoformat(),
            'calendar': 99999,
            'type': 'event'
        }
        response = self.client.post(
            reverse('prep_events'),
            data=json.dumps(invalid_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)
        self.assertIn('Calendar not found or access denied', response.json()['message'])