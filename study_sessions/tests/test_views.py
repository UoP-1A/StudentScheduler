import json

from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.utils import timezone

from datetime import timedelta, datetime
from rest_framework.test import APIClient

from users.models import CustomUser
from calendarapp.models import Calendar
from study_sessions.models import StudySession, StudySessionParticipant, RecurringStudySession
from study_sessions.forms import StudySessionForm, RecurringSessionForm

class StudySessionCreateViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.participant = CustomUser.objects.create_user(
            username='participant',
            password='testpass456'
        )
        
        # Create a calendar for the user
        self.calendar = Calendar.objects.create(
            user=self.user,
            name='Test Calendar',
        )
        
        self.url = reverse('study_sessions:create')
        
        # Use future date
        future_date = (timezone.now() + timedelta(days=7)).date()
        
        self.valid_data = {
            'title': 'Math Study Group',
            'description': 'Calculus review session',
            'date': future_date.strftime('%Y-%m-%d'),
            'start_time': '14:00',
            'end_time': '16:00',
            'participants': [self.participant.id],
            'is_recurring': False,
            'calendar_id': self.calendar.id  # Match the form field name
        }

    def test_create_view_get(self):
        """Test GET request to create view returns form"""
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], StudySessionForm)
        self.assertTemplateUsed(response, 'study_sessions/create.html')

    def test_create_valid_session(self):
        """Test creating a valid study session"""
        self.client.force_login(self.user)
        response = self.client.post(self.url, data=self.valid_data)
        
        # Should redirect to './' as per the view
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, './')
        
        # Verify session creation
        session = StudySession.objects.first()
        self.assertEqual(session.title, 'Math Study Group')
        self.assertEqual(session.host, self.user)
        
        # Verify participant was added
        self.assertEqual(StudySessionParticipant.objects.count(), 1)
        self.assertTrue(
            StudySessionParticipant.objects.filter(
                study_session=session,
                participant=self.participant
            ).exists()
        )

    def test_no_participants(self):
        """Test session creation without participants"""
        self.client.force_login(self.user)
        data = self.valid_data.copy()
        data['participants'] = []
        
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, './')
        self.assertEqual(StudySession.objects.count(), 1)
        self.assertEqual(StudySessionParticipant.objects.count(), 0)

    def test_unauthenticated_access(self):
        """Test unauthenticated users are redirected to login"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/accounts/login/'))

    def test_invalid_form_submission(self):
        """Test invalid form submission shows errors"""
        self.client.force_login(self.user)
        invalid_data = self.valid_data.copy()
        invalid_data['title'] = ''  # Make invalid
        
        response = self.client.post(self.url, data=invalid_data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['form'].is_valid())
        self.assertContains(response, "This field is required")
    
class CreateRecurringViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.calendar = Calendar.objects.create(
            user=self.user,
            name='Test Calendar'
        )
        
        # Create a test session with future date
        future_date = timezone.now().date() + timedelta(days=7)
        self.session = StudySession.objects.create(
            title='Math Study',
            description='Calculus review',
            date=future_date,
            start_time='14:00',
            end_time='16:00',
            is_recurring=True,
            host=self.user,
            calendar_id=self.calendar
        )
        self.url = reverse('study_sessions:create_recurring', args=[self.session.id])
        self.valid_data = {
            'recurrence_amount': 5  # 5 recurring sessions
        }

    def test_create_recurring_view_get(self):
        """Test GET request returns form"""
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], RecurringSessionForm)
        self.assertTemplateUsed(response, 'study_sessions/create_recurring.html')

    def test_create_valid_recurring_session(self):
        """Test creating valid recurring session"""
        self.client.force_login(self.user)
        response = self.client.post(self.url, data=self.valid_data)
        
        # Check redirect
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('index'))
        
        # Verify creation
        recurring = RecurringStudySession.objects.first()
        self.assertEqual(recurring.session_id, self.session)
        self.assertEqual(recurring.recurrence_amount, 5)

    def test_recurrence_amount_validation(self):
        """Test all recurrence amount validation cases"""
        self.client.force_login(self.user)
        
        # Test valid amount
        response = self.client.post(self.url, {'recurrence_amount': 3})
        self.assertEqual(response.status_code, 302)  # Should redirect on success
        
        # Test empty value
        response = self.client.post(self.url, {'recurrence_amount': ''})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Recurrence amount is required")
        
        # Test zero value
        response = self.client.post(self.url, {'recurrence_amount': 0})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "must be at least 1")
        
        # Test negative value
        response = self.client.post(self.url, {'recurrence_amount': -1})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "must be at least 1")
        
        # Test non-number value
        response = self.client.post(self.url, {'recurrence_amount': 'abc'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please enter a valid number")

    def test_unauthenticated_access(self):
        """Test unauthenticated users are redirected"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/accounts/login/'))

    def test_nonexistent_session(self):
        """Test with invalid session ID"""
        self.client.force_login(self.user)
        invalid_url = reverse('study_sessions:create_recurring', args=[9999])
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, 404)

    def test_non_recurring_session(self):
        """Test with session not marked as recurring"""
        future_date = timezone.now().date() + timedelta(days=7)
        non_recurring = StudySession.objects.create(
            title='One-time Session',
            date=future_date,
            start_time='10:00',
            end_time='12:00',
            is_recurring=False,
            host=self.user,
            calendar_id=self.calendar
        )
        url = reverse('study_sessions:create_recurring', args=[non_recurring.id])
        
        self.client.force_login(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_form_save(self):
        """Test form properly links to session"""
        form = RecurringSessionForm(data=self.valid_data)
        self.assertTrue(form.is_valid())
        
        recurring = form.save(commit=False)
        recurring.session_id = self.session
        recurring.save()
        
        self.assertEqual(recurring.session_id, self.session)
        self.assertEqual(recurring.recurrence_amount, 5)

class GetSessionsViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
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
        
        # Create test sessions
        self.session1 = StudySession.objects.create(
            title='Math Study',
            description='Calculus review',
            date=timezone.now().date() + timedelta(days=1),
            start_time='14:00',
            end_time='16:00',
            is_recurring=False,
            host=self.user,
            calendar_id=self.calendar
        )
        
        self.session2 = StudySession.objects.create(
            title='Physics Study',
            description='Quantum mechanics',
            date=timezone.now().date() + timedelta(days=2),
            start_time='10:00',
            end_time='12:00',
            is_recurring=True,
            host=self.user,
            calendar_id=self.calendar
        )
        
        # Create recurring session
        self.recurring_session = RecurringStudySession.objects.create(
            session_id=self.session2,
            recurrence_amount=3
        )
        
        # Add participant to session1
        StudySessionParticipant.objects.create(
            study_session=self.session1,
            participant=self.other_user
        )
        
        self.url = reverse('study_sessions:get_sessions')

    def test_get_sessions_authenticated(self):
        """Test authenticated user gets their sessions"""
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        sessions = response.json()
        self.assertEqual(len(sessions), 2)  # Both sessions
        
        # Verify session data
        math_session = next(s for s in sessions if s['title'] == 'Math Study')
        self.assertEqual(math_session['description'], 'Calculus review')
        self.assertEqual(math_session['model'], 'StudySession')
        self.assertEqual(math_session['type'], 'study')
        
        # Verify recurring session has rrule
        physics_session = next(s for s in sessions if s['title'] == 'Physics Study')
        self.assertIn('rrule', physics_session)
        self.assertIn('FREQ=WEEKLY', physics_session['rrule'])
        self.assertIn('COUNT=3', physics_session['rrule'])

    def test_get_sessions_participant(self):
        """Test participant gets sessions they're invited to"""
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        sessions = response.json()
        self.assertEqual(len(sessions), 2)  # Both sessions from earlier
        self.assertEqual(sessions[0]['title'], 'Math Study')

    def test_get_sessions_unauthenticated(self):
        """Test unauthenticated access is denied"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_session_datetime_format(self):
        """Test datetime fields are properly formatted"""
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        sessions = response.json()
        
        # Verify datetime formatting
        math_session = next(s for s in sessions if s['title'] == 'Math Study')
        start_datetime = datetime.strptime(math_session['start'], '%Y-%m-%dT%H:%M:%S%z')
        end_datetime = datetime.strptime(math_session['end'], '%Y-%m-%dT%H:%M:%S%z')
        
        # Verify duration calculation
        expected_duration = str(end_datetime - start_datetime)
        self.assertEqual(math_session['duration'], expected_duration)

    def test_non_recurring_session_rrule(self):
        """Test non-recurring sessions have COUNT=1 in rrule"""
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        sessions = response.json()
        
        math_session = next(s for s in sessions if s['title'] == 'Math Study')
        self.assertIn('rrule', math_session)
        self.assertIn('COUNT=1', math_session['rrule'])

    def test_recurring_session_rrule(self):
        """Test recurring sessions have correct recurrence count"""
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        sessions = response.json()
        
        physics_session = next(s for s in sessions if s['title'] == 'Physics Study')
        self.assertIn('rrule', physics_session)
        self.assertIn('COUNT=3', physics_session['rrule'])

class GetRecurringSessionsViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.calendar = Calendar.objects.create(
            user=self.user,
            name='Test Calendar'
        )
        
        # Create test sessions
        self.session1 = StudySession.objects.create(
            title='Math Study',
            date='2023-12-15',
            start_time='14:00',
            end_time='16:00',
            is_recurring=True,
            host=self.user,
            calendar_id=self.calendar
        )
        
        self.session2 = StudySession.objects.create(
            title='Physics Study',
            date='2023-12-16',
            start_time='10:00',
            end_time='12:00',
            is_recurring=True,
            host=self.user,
            calendar_id=self.calendar
        )
        
        # Create recurring sessions
        self.recurring1 = RecurringStudySession.objects.create(
            session_id=self.session1,
            recurrence_amount=5
        )
        self.recurring2 = RecurringStudySession.objects.create(
            session_id=self.session2,
            recurrence_amount=3
        )
        
        self.url = reverse('study_sessions:get_recurring_sessions')

    def test_get_all_recurring_sessions(self):
        """Test retrieving all recurring sessions"""
        self.client.force_login(self.user)

        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        sessions = json.loads(response.content)
        
        self.assertEqual(len(sessions), 2)
        
        # Verify first session
        session1_data = next(s for s in sessions if s['id'] == self.recurring1.id)
        self.assertEqual(session1_data['recurrence_amount'], 5)
        self.assertEqual(session1_data['session_id'], self.session1.id)
        
        # Verify second session
        session2_data = next(s for s in sessions if s['id'] == self.recurring2.id)
        self.assertEqual(session2_data['recurrence_amount'], 3)
        self.assertEqual(session2_data['session_id'], self.session2.id)

    def test_empty_recurring_sessions(self):
        """Test when no recurring sessions exist"""
        self.client.force_login(self.user)

        RecurringStudySession.objects.all().delete()
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        sessions = json.loads(response.content)
        self.assertEqual(len(sessions), 0)

    def test_response_structure(self):
        """Test response has correct structure"""
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        sessions = json.loads(response.content)
        
        # Verify each session has required fields
        for session in sessions:
            self.assertIn('id', session)
            self.assertIn('recurrence_amount', session)
            self.assertIn('session_id', session)
            self.assertIsInstance(session['id'], int)
            self.assertIsInstance(session['recurrence_amount'], int)
            self.assertIsInstance(session['session_id'], int)

    def test_unauthenticated_access(self):
        """Test unauthenticated access is allowed"""
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_authenticated_access(self):
        """Test authenticated access works"""
        self.client.force_login(self.user)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        sessions = json.loads(response.content)
        self.assertEqual(len(sessions), 2)

    def test_session_ordering(self):
        """Test sessions are ordered by ID"""
        self.client.force_login(self.user)
        # Create another session to test ordering
        session3 = StudySession.objects.create(
            title='Chemistry Study',
            date='2023-12-17',
            start_time='09:00',
            end_time='11:00',
            is_recurring=True,
            host=self.user,
            calendar_id=self.calendar
        )
        recurring3 = RecurringStudySession.objects.create(
            session_id=session3,
            recurrence_amount=2
        )
        
        response = self.client.get(self.url)
        sessions = json.loads(response.content)
        
        # Verify sessions are ordered by ID
        self.assertEqual(sessions[0]['id'], self.recurring1.id)
        self.assertEqual(sessions[1]['id'], self.recurring2.id)
        self.assertEqual(sessions[2]['id'], recurring3.id)