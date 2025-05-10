from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from notifications.models import Notification

CustomUser = get_user_model()

class NotificationsViewTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.other_user = CustomUser.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        self.url = reverse('notifications')
        
        # Create test notifications
        Notification.objects.create(
            user=self.user,
            message="First notification"
        )
        Notification.objects.create(
            user=self.user,
            message="Second notification"
        )
        Notification.objects.create(
            user=self.other_user,
            message="Other user's notification"
        )

    def test_authenticated_user_with_notifications(self):
        """Test view with existing notifications"""
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'notifications/notifications.html')
        
        notifications = response.context['notificationsList']
        self.assertEqual(notifications.count(), 2)
        self.assertEqual(notifications[1].message, "Second notification")
        self.assertEqual(notifications[0].message, "First notification")
        self.assertContains(response, "Second notification")

    def test_authenticated_user_no_notifications(self):
        """Test view with no notifications"""
        Notification.objects.all().delete()
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['notificationsList']), 0)
        self.assertContains(response, "No new notifications.")

    def test_unauthenticated_user(self):
        """Test authentication requirement"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            f'/accounts/login/?next={self.url}'
        )

    def test_notification_ordering(self):
        """Test notifications are ordered by timestamp"""
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        notifications = response.context['notificationsList']
        
        # Verify descending order
        self.assertTrue(
            notifications[0].timestamp <= notifications[1].timestamp
        )

class MarkAsReadViewTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.other_user = CustomUser.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        self.notification = Notification.objects.create(
            user=self.user,
            message="Test notification",
            is_read=False
        )
        self.url = reverse('mark_as_read', args=[self.notification.id])

    def test_authenticated_user_can_mark_read(self):
        """Test successful status update"""
        self.client.force_login(self.user)
        response = self.client.post(self.url)
        
        updated_notification = Notification.objects.get(id=self.notification.id)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('notifications'))
        self.assertTrue(updated_notification.is_read)

    def test_invalid_notification_id(self):
        """Test non-existent notification"""
        self.client.force_login(self.user)
        invalid_url = reverse('mark_as_read', args=[999])
        response = self.client.post(invalid_url)
        self.assertEqual(response.status_code, 404)

    def test_cannot_mark_others_notification(self):
        """Test ownership verification"""
        self.client.force_login(self.other_user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 404)
        self.assertFalse(Notification.objects.get(id=self.notification.id).is_read)

    def test_unauthenticated_user(self):
        """Test authentication requirement"""
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            f'/accounts/login/?next={self.url}'
        )

    def test_get_request_not_allowed(self):
        """Test HTTP method enforcement"""
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)