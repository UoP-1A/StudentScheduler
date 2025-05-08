from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from ..models import StudySession, CustomUser, Calendar, RecurringStudySession, StudySessionParticipant

class StudySessionModelTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.calendar = Calendar.objects.create(
            user=self.user,
            name='Test Calendar'
        )
        self.tomorrow = timezone.now().date() + timezone.timedelta(days=1)

    def test_study_session_creation(self):
        """Test basic model creation"""
        session = StudySession.objects.create(
            host=self.user,
            title='Math Study Group',
            description='Calculus review session',
            start_time='14:00:00',
            end_time='16:00:00',
            date=self.tomorrow,
            is_recurring=False,
            calendar_id=self.calendar
        )
        
        self.assertEqual(session.host, self.user)
        self.assertEqual(session.title, 'Math Study Group')
        self.assertEqual(str(session), f"{self.user.username} - Math Study Group")

    def test_time_validation(self):
        """Test end_time > start_time validation"""
        with self.assertRaises(ValidationError):
            session = StudySession(
                host=self.user,
                title='Invalid Session',
                description='This should fail',
                start_time='16:00:00',
                end_time='14:00:00',  # End before start
                date=self.tomorrow,
                calendar_id=self.calendar
            )
            session.full_clean()

    def test_date_validation(self):
        """Test future date requirement"""
        yesterday = timezone.now().date() - timezone.timedelta(days=1)
        with self.assertRaises(ValidationError):
            session = StudySession(
                host=self.user,
                title='Past Session',
                description='This should fail',
                start_time='14:00:00',
                end_time='16:00:00',
                date=yesterday,  # Past date
                calendar_id=self.calendar
            )
            session.full_clean()

    def test_host_relationship(self):
        """Test host foreign key relationship"""
        session = StudySession.objects.create(
            host=self.user,
            title='Relationship Test',
            description='Testing user links',
            start_time='10:00:00',
            end_time='11:00:00',
            date=self.tomorrow,
            calendar_id=self.calendar
        )
        self.assertEqual(self.user.study_sessions.first(), session)

    def test_calendar_relationship(self):
        """Test calendar foreign key relationship"""
        session = StudySession.objects.create(
            host=self.user,
            title='Calendar Test',
            description='Testing calendar links',
            start_time='09:00:00',
            end_time='10:00:00',
            date=self.tomorrow,
            calendar_id=self.calendar
        )
        self.assertEqual(self.calendar.study_sessions.first(), session)

class RecurringStudySessionModelTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.calendar = Calendar.objects.create(
            user=self.user,
            name='Test Calendar'
        )
        self.study_session = StudySession.objects.create(
            host=self.user,
            title='Weekly Math Study',
            description='Recurring session',
            start_time='14:00:00',
            end_time='16:00:00',
            date=timezone.now().date() + timezone.timedelta(days=1),
            is_recurring=True,
            calendar_id=self.calendar
        )

    def test_recurring_session_creation(self):
        """Test basic model creation"""
        recurring_session = RecurringStudySession.objects.create(
            session_id=self.study_session,
            recurrence_amount=5
        )
        
        self.assertEqual(recurring_session.session_id, self.study_session)
        self.assertEqual(recurring_session.recurrence_amount, 5)
        self.assertEqual(
            str(recurring_session),
            f"{self.user.username} - Weekly Math Study x 5"
        )

    def test_negative_recurrence_amount(self):
        """Test positive amount validation"""
        with self.assertRaises(ValidationError):
            session = RecurringStudySession(
                session_id=self.study_session,
                recurrence_amount=-3
            )
            session.full_clean()

    def test_zero_recurrence_amount(self):
        """Test non-zero amount validation"""
        with self.assertRaises(ValidationError):
            session = RecurringStudySession(
                session_id=self.study_session,
                recurrence_amount=0
            )
            session.full_clean()

    def test_session_relationship(self):
        """Test study session foreign key relationship"""
        recurring_session = RecurringStudySession.objects.create(
            session_id=self.study_session,
            recurrence_amount=4
        )
        self.assertEqual(
            self.study_session.recurring_sessions.first(),
            recurring_session
        )

class StudySessionParticipantModelTests(TestCase):
    def setUp(self):
        # Create test user
        self.user1 = CustomUser.objects.create_user(
            username='participant1',
            password='testpass123'
        )
        self.user2 = CustomUser.objects.create_user(
            username='participant2', 
            password='testpass123'
        )
        
        # Create test study session
        self.host = CustomUser.objects.create_user(
            username='hostuser',
            password='hostpass123'
        )
        self.calendar = Calendar.objects.create(
            user=self.host,
            name='Host Calendar'
        )
        self.study_session = StudySession.objects.create(
            host=self.host,
            title='Math Study Group',
            start_time='14:00:00',
            end_time='16:00:00',
            date=timezone.now().date() + timezone.timedelta(days=1),
            calendar_id=self.calendar
        )

    def test_participant_creation(self):
        """Test basic model creation"""
        participant = StudySessionParticipant.objects.create(
            study_session=self.study_session,
            participant=self.user1
        )
        
        self.assertEqual(participant.study_session, self.study_session)
        self.assertEqual(participant.participant, self.user1)
        self.assertEqual(
            str(participant),
            f"{self.user1.username} - {self.study_session.title}"
        )

    def test_study_session_relationship(self):
        """Test session foreign key relationship"""
        participant = StudySessionParticipant.objects.create(
            study_session=self.study_session,
            participant=self.user1
        )
        self.assertEqual(
            self.study_session.participants_set.first(),
            participant
        )
        self.assertEqual(self.study_session.participants_set.count(), 1)

    def test_participant_relationship(self):
        """Test user foreign key relationship"""
        participant = StudySessionParticipant.objects.create(
            study_session=self.study_session,
            participant=self.user1
        )
        self.assertEqual(
            self.user1.study_sessions_participated.first(),
            participant
        )

    def test_duplicate_participation(self):
        """Test unique participant per session"""
        StudySessionParticipant.objects.create(
            study_session=self.study_session,
            participant=self.user1
        )
        
        with self.assertRaises(ValidationError):
            StudySessionParticipant.objects.create(
                study_session=self.study_session,
                participant=self.user1
            )
            
        duplicate = StudySessionParticipant(
            study_session=self.study_session,
            participant=self.user1
        )
        with self.assertRaises(ValidationError):
            duplicate.full_clean()

    def test_cascade_deletion(self):
        """Test session deletion cascades to participants"""
        participant = StudySessionParticipant.objects.create(
            study_session=self.study_session,
            participant=self.user1
        )
        self.study_session.delete()
        with self.assertRaises(StudySessionParticipant.DoesNotExist):
            participant.refresh_from_db()