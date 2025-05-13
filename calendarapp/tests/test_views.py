import json

from django.test import TestCase, RequestFactory, Client
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone
from django.utils.timezone import make_aware

from datetime import timedelta, datetime
from rest_framework.test import APIRequestFactory

from calendarapp.views import delete_calendar
from calendarapp.models import Calendar, Event
from study_sessions.models import StudySession

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


class UpdateEventViewTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser', 
            password='testpass123',
        )
        self.other_user = CustomUser.objects.create_user(
            username='otheruser',
            password='testpass456',
        )
        
        self.calendar = Calendar.objects.create(user=self.user, name='Test Calendar')
        self.event = Event.objects.create(
            calendar=self.calendar,
            title='Test Event',
            start=make_aware(datetime(2023, 1, 1, 10, 0)),
            end=make_aware(datetime(2023, 1, 1, 11, 0))
        )
        self.url = reverse('update_event')
        self.client.login(username='testuser', password='testpass123')

    def test_update_event_success(self):
        """Test successful event update"""
        data = {
            'id': self.event.id,
            'start': '2023-01-02T10:00:00Z',
            'end': '2023-01-02T11:00:00Z',
            'model': 'event'
        }
        
        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertEqual(response_data['status'], 'success')
        self.assertEqual(response_data['event_id'], self.event.id)
        
        self.event.refresh_from_db()
        self.assertEqual(
            self.event.start.isoformat(),
            '2023-01-02T10:00:00+00:00'
        )
        self.assertEqual(
            self.event.end.isoformat(),
            '2023-01-02T11:00:00+00:00'
        )

    def test_update_event_end_optional(self):
        """Test that duration is maintained when updating start time"""
        # Create event with explicit 2-hour duration
        event = Event.objects.create(
            calendar=self.calendar,
            title='Test Event',
            start=make_aware(datetime(2023, 1, 1, 10, 0)),
            end=make_aware(datetime(2023, 1, 1, 12, 0)),  # 2 hour duration
            duration=timedelta(hours=2),
        )
        
        # Verify initial setup
        self.assertEqual(event.duration, timedelta(hours=2))

        # Update just the start time
        response = self.client.post(
            self.url,
            data=json.dumps({
                'id': event.id,
                'start': '2023-01-02T10:00:00Z',
                'model': 'event'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        event.refresh_from_db()
        
        # Verify duration was maintained
        self.assertEqual(event.duration, timedelta(hours=2))
        self.assertIsNotNone(event.end, "End time should not be None")
        self.assertEqual(
            event.end.isoformat(),
            '2023-01-02T12:00:00+00:00'  # 10:00 + 2 hours
        )

    def test_update_event_invalid_datetime(self):
        """Test with invalid datetime format"""
        data = {
            'id': self.event.id,
            'start': 'invalid-datetime',
            'model': 'event'
        }
        
        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        content = response.json()
        self.assertEqual(content['status'], 'error')
        self.assertIn('datetime', content['message'].lower())

    def test_update_event_permission_denied(self):
        """Test updating another user's event"""
        self.client.logout()
        self.client.login(username='otheruser', password='testpass456')
        
        data = {
            'id': self.event.id,
            'start': '2023-01-02T10:00:00Z',
            'model': 'event'
        }
        
        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {
            'status': 'error',
            'message': 'Permission denied'
        })

    def test_update_event_missing_id(self):
        """Test missing event ID"""
        data = {
            'start': '2023-01-02T10:00:00Z',
            'model': 'event'
        }
        
        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {
            'status': 'error',
            'message': 'Missing required fields'
        })

    def test_update_event_missing_start(self):
        """Test missing start time"""
        data = {
            'id': self.event.id,
            'model': 'event'
        }
        
        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {
            'status': 'error',
            'message': 'Missing required fields'
        })

    def test_update_event_not_found(self):
        """Test with non-existent event ID"""
        data = {
            'id': 9999,
            'start': '2023-01-02T10:00:00Z',
            'model': 'event'
        }
        
        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {
            'status': 'error',
            'message': 'Event not found'
        })

    def test_update_event_missing_model(self):
        """Test missing model type"""
        data = {
            'id': self.event.id,
            'start': '2023-01-02T10:00:00Z'
        }
        
        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {
            'status': 'error',
            'message': 'Missing required fields'
        })

class DeleteCalendarViewTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.other_user = CustomUser.objects.create_user(
            username='otheruser',
            password='testpass456'
        )
        self.calendar = Calendar.objects.create(
            user=self.user,
            name='Test Calendar'
        )
        self.url = reverse('delete_calendar', args=[self.calendar.id])

    def test_delete_calendar_success(self):
        """Test successful calendar deletion by owner"""
        request = self.factory.post(self.url)
        request.user = self.user
        
        # Setup messages framework
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        
        response = delete_calendar(request, self.calendar.id)
        
        # Check calendar was deleted
        with self.assertRaises(Calendar.DoesNotExist):
            Calendar.objects.get(id=self.calendar.id)
        
        # Check response redirects to profile
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('profile'))
        
        # Check success message
        messages = list(messages)
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Calendar deleted successfully.")

    def test_delete_calendar_not_found(self):
        """Test deleting non-existent calendar"""
        request = self.factory.post(self.url)
        request.user = self.user
        
        # Change to test the actual behavior of get_object_or_404
        response = delete_calendar(request, 9999)  # Non-existent ID
        self.assertEqual(response.status_code, 404)

    def test_delete_calendar_permission_denied(self):
        """Test deleting another user's calendar"""
        request = self.factory.post(self.url)
        request.user = self.other_user  # Different user
        
        response = delete_calendar(request, self.calendar.id)
        
        # Calendar should still exist
        calendar = Calendar.objects.get(id=self.calendar.id)
        self.assertEqual(calendar.name, 'Test Calendar')
        
        # Should return 404 since get_object_or_404 checks owner
        self.assertEqual(response.status_code, 404)

    def test_delete_calendar_requires_login(self):
        """Test anonymous user can't delete calendar"""
        request = self.factory.post(self.url)
        request.user = AnonymousUser()
        
        response = delete_calendar(request, self.calendar.id)
        
        # Should redirect to login page
        self.assertEqual(response.status_code, 302)
        login_url = reverse('login')  # Make sure this matches your login URL name
        self.assertTrue(response.url.startswith(login_url))
        
        # Calendar should still exist
        calendar = Calendar.objects.get(id=self.calendar.id)
        self.assertEqual(calendar.name, 'Test Calendar')
        
class SearchResultsViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpassword'
        )
        self.calendar = Calendar.objects.create(user=self.user, name='Test User')  # Create a single calendar

        self.event1 = Event.objects.create(
            title="Math Lecture",
            start=make_aware(datetime(2025, 5, 15, 10, 0)),
            calendar=self.calendar
        )
        self.event2 = Event.objects.create(
            title="Science Workshop",
            start=make_aware(datetime(2025, 5, 16, 12, 0)),
            calendar=self.calendar
        )
        self.session1 = StudySession.objects.create(
            title="Study Group - Software Engineering",
            start_time=make_aware(datetime(2025, 5, 17, 15, 0)).time(),
            end_time=make_aware(datetime(2025, 5, 17, 17, 0)).time(),
            date=make_aware(datetime(2025, 5, 17)).date(),
            calendar_id=self.calendar, 
            host=self.user
        )
        self.url = reverse('search_results')

    def test_search_results_no_input(self):
        """Test search results without input (should return empty results)"""
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'search_results.html')
        self.assertIsNone(response.context['query'])
        self.assertEqual(len(response.context['event_results']), 0)
        self.assertEqual(len(response.context['session_results']), 0)

    def test_search_results_valid_query(self):
        """Test search results with a valid query (should match events and sessions)"""
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(self.url + '?q=Math')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['query'], "Math")
        self.assertEqual(len(response.context['event_results']), 1)
        self.assertEqual(len(response.context['session_results']), 0)

    def test_search_results_non_matching_query(self):
        """Test search results with a non-matching query (should return empty results)"""
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(self.url + '?q=History')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['event_results']), 0)
        self.assertEqual(len(response.context['session_results']), 0)

    def test_search_results_partial_query(self):
        """Test search results with a partial query (should match relevant results)"""
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(self.url + '?q=Study')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['session_results']), 1)
        self.assertEqual(len(response.context['event_results']), 0)

    def test_search_results_case_insensitive(self):
        """Test search results are case-insensitive"""
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(self.url + '?q=math')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['event_results']), 1)
        self.assertEqual(len(response.context['session_results']), 0)

    def test_search_results_date_query(self):
        """Test search results using date as query (should match date results)"""
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(self.url + '?q=2025-05-15')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['event_results']), 1)
        self.assertEqual(len(response.context['session_results']), 0)
        
    def test_search_results_requires_login(self):
        """Test that search results view requires authentication"""
        response = self.client.get(self.url + '?q=Math')
        self.assertEqual(response.status_code, 302)  # Redirect to login
        self.assertTrue(response.url.startswith(reverse('login')))