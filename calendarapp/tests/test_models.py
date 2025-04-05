from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from calendarapp.models import Calendar

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
    
    def test_blank_name_cannot_be_saved(self):
        """
        Test blank name cannot be saved to database"
        """
        calendar = Calendar(user=self.user, name='')
        with self.assertRaises(ValidationError) as cm:
            calendar.full_clean()
