from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta

from calendarapp.models import Calendar, Event


CustomUser = get_user_model()

class CalendarModelTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_create_calendar_with_required_fields(self):
        """
        Test creating a calendar with all required fields succeeds
        """
        calendar = Calendar.objects.create(
            user=self.user,
            name='Test Calendar'
        )
        self.assertEqual(calendar.user, self.user)
        self.assertEqual(calendar.name, 'Test Calendar')
        self.assertIsNotNone(calendar.created_at)
    
    def test_calendar_foreign_key_relationship(self):
        """
        Test the ForeignKey relationship to CustomUser and related_name
        """
        calendar = Calendar.objects.create(
            user=self.user,
            name='Test Calendar'
        )
        self.assertEqual(calendar.user, self.user)
        self.assertIn(calendar, self.user.calendars.all())
    
    def test_name_max_length_valid(self):
        """
        Test that a name with exactly 255 characters is valid
        """
        valid_name = 'x' * 255
        calendar = Calendar(user=self.user, name=valid_name)
        try:
            calendar.full_clean()  # Explicit validation
        except ValidationError:
            self.fail("255-character name should be valid")


    def test_name_exceeding_max_length_invalid(self):
        """
        Test that a name longer than 255 characters is rejected
        """
        invalid_name = 'x' * 256
        calendar = Calendar(user=self.user, name=invalid_name)
        with self.assertRaises(ValidationError) as cm:
            calendar.full_clean()
        
        self.assertIn('name', cm.exception.message_dict)
        self.assertIn('Ensure this value has at most 255 characters', 
                    str(cm.exception.message_dict['name'][0]))
    
    def test_created_at_auto_now_add(self):
        """
        Test created_at is automatically set on creation
        """
        calendar = Calendar.objects.create(
            user=self.user,
            name='Test Calendar'
        )
        self.assertIsNotNone(calendar.created_at)
    
    def test_created_at_not_updated_on_save(self):
        """
        Test created_at shouldn't change when calendar is updated
        """
        calendar = Calendar.objects.create(
            user=self.user,
            name='Test Calendar'
        )
        original_created_at = calendar.created_at
        calendar.name = 'Updated Name'
        calendar.save()
        self.assertEqual(calendar.created_at, original_created_at)
    
    def test_str_representation(self):
        """
        Test the __str__ method returns the correct format
        """
        calendar = Calendar.objects.create(
            user=self.user,
            name='Test Calendar'
        )
        expected_str = f"{self.user.username} - Test Calendar"
        self.assertEqual(str(calendar), expected_str)
    
    def test_user_delete_cascades_to_calendar(self):
        """
        Test deleting the user deletes the associated calendar
        """
        calendar = Calendar.objects.create(
            user=self.user,
            name='Test Calendar'
        )
        self.user.delete()
        with self.assertRaises(Calendar.DoesNotExist):
            Calendar.objects.get(pk=calendar.pk)
    
    def test_name_cannot_be_blank(self):
        """
        Test name cannot be an empty string
        """
        calendar = Calendar(user=self.user, name='')
        with self.assertRaises(ValidationError) as cm:
            calendar.full_clean()
        self.assertIn('name', cm.exception.message_dict)
    
    def test_user_is_required(self):
        """
        Test user field cannot be empty
        """
        calendar = Calendar(name='Test Calendar')
        with self.assertRaises(ValidationError) as cm:
            calendar.full_clean()
        self.assertIn('user', cm.exception.message_dict)

class EventModelTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.calendar = Calendar.objects.create(
            user=self.user,
            name='Test Calendar'
        )
        self.now = timezone.now()
        self.tomorrow = self.now + timedelta(days=1)

    def test_create_event_with_required_fields(self):
        """
        Test creating an event with required fields
        """
        event = Event.objects.create(
            calendar=self.calendar,
            title='Test Event',
            start=self.now
        )
        self.assertEqual(event.calendar, self.calendar)
        self.assertEqual(event.title, 'Test Event')
        self.assertEqual(event.start, self.now)
        self.assertEqual(event.type, 'event')

    def test_event_foreign_key_relationship(self):
        """
        Test the ForeignKey relationship to Calendar
        """
        event = Event.objects.create(
            calendar=self.calendar,
            title='Test Event',
            start=self.now
        )
        self.assertEqual(event.calendar, self.calendar)
        self.assertIn(event, self.calendar.event_set.all())

    # Field Validation Tests
    def test_title_required(self):
        """
        Test title cannot be blank
        """
        event = Event(
            calendar=self.calendar,
            title='',
            start=self.now
        )
        with self.assertRaises(ValidationError):
            event.full_clean()

    def test_start_required(self):
        """
        Test start cannot be null
        """
        event = Event(
            calendar=self.calendar,
            title='Test Event',
            start=None
        )
        with self.assertRaises(ValidationError):
            event.full_clean()

    def test_valid_event_type(self):
        """
        Test type field accepts valid choices
        """
        valid_event = Event(
            calendar=self.calendar,
            title='Valid Event',
            start=self.now,
            type='event'
        )
        valid_event.full_clean()
    
    def test_invalid_event_type(self):
        """
        Test type field does not accept invalid choices
        """
        invalid_event = Event(
            calendar=self.calendar,
            title='Invalid Event',
            start=self.now,
            type='invalid'
        )
        with self.assertRaises(ValidationError):
            invalid_event.full_clean()

    def test_save_with_string_dates(self):
        """
        Test string dates are converted to datetime objects
        """
        event = Event(
            calendar=self.calendar,
            title='String Dates',
            start=str(self.now),
            end=str(self.tomorrow)
        )
        event.save()
        self.assertIsInstance(event.start, timezone.datetime)
        self.assertIsInstance(event.end, timezone.datetime)

    def test_duration_calculation(self):
        """
        Test duration is calculated from start and end when not set
        """
        event = Event(
            calendar=self.calendar,
            title='Duration Test',
            start=self.now,
            end=self.tomorrow
        )
        event.save()
        self.assertEqual(event.duration, timedelta(days=1))

    def test_duration_not_overwritten(self):
        """
        Test that a manually set duration sets the end date appropriately.
        """
        custom_duration = timedelta(hours=2)
        event = Event(
            calendar=self.calendar,
            title='Custom Duration',
            start=self.now,
            end=self.tomorrow,
            duration=custom_duration
        )
        event.save()
        self.assertEqual(event.duration, custom_duration)

    # Edge Cases
    def test_end_before_start(self):
        """
        Test end cannot be before start
        """
        event = Event(
            calendar=self.calendar,
            title='Invalid Times',
            start=self.tomorrow,
            end=self.now
        )
        with self.assertRaises(ValidationError):
            event.full_clean()

    def test_rrule_optional(self):
        """
        Test rrule can be null/blank
        """
        event = Event.objects.create(
            calendar=self.calendar,
            title='No RRule',
            start=self.now,
            rrule=None
        )
        try:
            event.full_clean()
        except ValidationError:
            self.fail("rrule=None should be valid")

    def test_description_optional(self):
        """
        Test description can be blank
        """
        event = Event.objects.create(
            calendar=self.calendar,
            title='No Description',
            start=self.now,
            description=''
        )
        try:
            event.full_clean()
        except ValidationError:
            self.fail("Empty description should be valid")

    def test_type_default(self):
        """
        Test type defaults to event
        """
        event = Event.objects.create(
            calendar=self.calendar,
            title='Default Type',
            start=self.now
        )
        self.assertEqual(event.type, 'event')

    def test_type_choices_values(self):
        """
        Test all type choices are valid
        """
        for choice in Event.Types.values:
            event = Event(
                calendar=self.calendar,
                title=f'{choice} Event',
                start=self.now,
                type=choice
            )
            try:
                event.full_clean()
            except ValidationError:
                self.fail(f"Type '{choice}' should be valid")
