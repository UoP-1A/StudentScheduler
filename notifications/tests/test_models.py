from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from ..models import Notification

CustomUser = get_user_model()

class NotificationModelTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.sample_message = "This is an important notification"

    def test_notification_creation(self):
        """Test basic notification creation"""
        notification = Notification.objects.create(
            user=self.user,
            message=self.sample_message
        )
        
        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.message, self.sample_message)
        self.assertFalse(notification.is_read)
        self.assertIsNotNone(notification.timestamp)
        self.assertTrue(notification.timestamp <= timezone.now())

    def test_str_representation_short(self):
        """Test string representation with short message"""
        notification = Notification.objects.create(
            user=self.user,
            message="Short message"
        )
        self.assertEqual(
            str(notification),
            f"Notification for {self.user.username}: Short message"
        )

    def test_str_representation_long(self):
        """Test string truncation for long messages"""
        long_message = "This is a very long notification message that should be truncated"
        notification = Notification.objects.create(
            user=self.user,
            message=long_message
        )
        self.assertEqual(
            str(notification),
            f"Notification for {self.user.username}: {long_message[:30]}"
        )

    def test_mark_as_read(self):
        """Test notification status change"""
        notification = Notification.objects.create(
            user=self.user,
            message=self.sample_message
        )
        notification.is_read = True
        notification.save()
        
        updated_notification = Notification.objects.get(id=notification.id)
        self.assertTrue(updated_notification.is_read)

    def test_user_relationship(self):
        """Test multiple notifications for a user"""
        Notification.objects.create(
            user=self.user,
            message="First notification"
        )
        Notification.objects.create(
            user=self.user,
            message="Second notification"
        )
        
        user_notifications = Notification.objects.filter(user=self.user)
        self.assertEqual(user_notifications.count(), 2)
        self.assertEqual(user_notifications[0].user, self.user)
        self.assertEqual(user_notifications[1].user, self.user)