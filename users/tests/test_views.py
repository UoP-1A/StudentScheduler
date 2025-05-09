from django.test import TestCase, RequestFactory, Client
from django.urls import reverse
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth import get_user_model
from django.conf import settings

from users.forms import RegisterForm, LoginForm, FriendRequest
from users.views import CustomLoginView

CustomUser = get_user_model()

class ProfileViewTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="testuser",
            password="testpassword"
        )
    
    def test_require_authentication(self):
        """Ensure that profile page requires you to be authenticated"""
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/accounts/login/?next=/accounts/profile/')

    def test_authenticated_user(self):
        """Ensure an authenticated user can visit their profile"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/profile.html")

    def test_from_profile_flag_set(self):
        """Ensure the flag from_profile is set to allow for access to account deletion"""
        self.client.force_login(self.user)
        self.client.get(reverse("profile"))
        is_set = self.client.session.get("from_profile")
        self.assertEqual(is_set, True)

class DeleteAccountConfirmationViewTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser', 
            password='testpass123'
        )
        self.url = reverse('delete_account_confirmation')
        
    def test_requires_login(self):
        """Test that the view requires login"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)  # Should redirect to login
        
    def test_redirects_if_not_from_profile(self):
        """Test redirects if session d  oesn't have 'from_profile' flag"""
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/profile')
        
    def test_successful_access_with_from_profile_flag(self):
        """Test successful access when coming from profile"""
        self.client.force_login(self.user)
        session = self.client.session
        session['from_profile'] = True
        session.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/delete_account_confirmation.html')
        
    def test_sets_can_delete_account_session_flag(self):
        """Test that the view sets the can_delete_account session flag"""
        self.client.force_login(self.user)
        session = self.client.session
        session['from_profile'] = True
        session.save()
        self.client.get(self.url)
        self.assertTrue(self.client.session.get('can_delete_account', False))

class DeleteAccountViewTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.url = reverse('delete_account') 

    def test_requires_login(self):
        """Test that the view requires login"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)  # Should redirect to login

    def test_redirects_if_not_from_confirmation(self):
        """Test redirects if session doesn't have 'can_delete_account' flag"""
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/profile')

    def test_redirects_on_get_request(self):
        """Test that GET requests are redirected to profile"""
        self.client.force_login(self.user)
        session = self.client.session
        session['can_delete_account'] = True
        session.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/profile')

    def test_deletes_account_on_post(self):
        """Test that POST request deletes the user account"""
        self.client.force_login(self.user)
        session = self.client.session
        session['can_delete_account'] = True
        session.save()

        # Verify user exists before deletion
        self.assertTrue(CustomUser.objects.filter(pk=self.user.pk).exists())
        
        response = self.client.post(self.url)
        
        # Verify redirect after deletion
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')
        
        # Verify user is deleted
        self.assertFalse(CustomUser.objects.filter(pk=self.user.pk).exists())
        
        # Verify session flag is cleared
        self.assertFalse(self.client.session.get('can_delete_account', False))

    def test_prevents_deletion_without_session_flag(self):
        """Test that account isn't deleted without session flag"""
        self.client.force_login(self.user)
        
        # Don't set the session flag
        response = self.client.post(self.url)
        
        # Should redirect to profile
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/profile')
        
        # User should still exist
        self.assertTrue(CustomUser.objects.filter(pk=self.user.pk).exists())

class RegisterViewTests(TestCase):
    def setUp(self):
        self.url = reverse('register')
        self.valid_data = {
            'first_name': 'test',
            'last_name': 'user',
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'complexpassword123',
            'password2': 'complexpassword123',
        }

    def test_get_request_returns_form(self):
        """Test that GET request returns form with initial values"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/register.html')
        self.assertIsInstance(response.context['form'], RegisterForm)
        self.assertEqual(response.context['form'].initial, {'key': 'value'})

    def test_valid_post_creates_user_and_redirects(self):
        """Test that valid POST creates user and redirects to home"""
        response = self.client.post(self.url, data=self.valid_data)
        
        # Check redirect
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')
        
        # Check user creation
        self.assertTrue(CustomUser.objects.filter(username='testuser').exists())
        user = CustomUser.objects.get(username='testuser')
        self.assertEqual(user.email, 'test@example.com')

    def test_invalid_post_returns_form_with_errors(self):
        """Test that invalid POST returns form with errors"""
        invalid_data = self.valid_data.copy()
        invalid_data['password2'] = 'differentpassword'  # Make passwords mismatch
        
        response = self.client.post(self.url, data=invalid_data)
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/register.html')
        
        # Check form errors
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)  # Should have password mismatch error

    def test_authenticated_user_redirected(self):
        """Test that authenticated users are redirected away from registration"""
        CustomUser.objects.create_user(username='existing', password='testpass123')
        self.client.login(username='existing', password='testpass123')
        
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(response.url, reverse("profile")) 

    def test_password_is_hashed(self):
        """Test that the password is properly hashed"""
        self.client.post(self.url, data=self.valid_data)
        user = CustomUser.objects.get(username='testuser')
        self.assertNotEqual(user.password, 'complexpassword123')  # Should be hashed
        self.assertTrue(user.check_password('complexpassword123'))  # Should verify correctly
    
class CustomLoginViewTests(TestCase):
    def setUp(self):
        self.username = 'testuser'
        self.password = 'testpassword123'
        self.user = CustomUser.objects.create_user(
            username=self.username,
            email='test@example.com',
            password=self.password,
            is_active=True
        )
        
        self.factory = RequestFactory()
        self.client = Client()
        
        self.login_url = reverse('login')
        self.success_url = '/'
    
    def test_login_form_with_remember_me_checked(self):
        """Test that when 'remember_me' is checked, session uses SESSION_COOKIE_AGE."""
        response = self.client.post(self.login_url, {
            'username': self.username, 
            'password': self.password,
            'remember_me': True
        }, follow=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['user'].is_authenticated)
        self.assertEqual(
            self.client.session.get_expiry_age(),
            settings.SESSION_COOKIE_AGE
        )
    
    def test_form_valid_method_directly(self):
        """Test the form_valid method."""
        request = self.factory.post(self.login_url, {
            'username': self.username,
            'password': self.password,
            "remember_me": True,
        })
        
        # Create a form with cleaned_data (remember_me=False)
        form = LoginForm(data={
            'username': self.username,
            'password': self.password,
            'remember_me': True,
        })
        form.is_valid()  # Run validation

        # Add session middleware
        middleware = SessionMiddleware(lambda request: None)
        middleware.process_request(request)
        request.session.save()
        
        
        # Create view instance and test form_valid method
        view = CustomLoginView()
        view.request = request
        view.setup(request)
        view.success_url = self.success_url
        
        response = view.form_valid(form)
        
        self.assertEqual(request.session.get_expiry_age(), 86400)
        self.assertTrue(request.session.modified)

    def test_successful_login_redirect(self):
        """Test that successful login redirects to success URL"""
        response = self.client.post(self.login_url, {
            'username': self.username,
            'password': self.password,
            'remember_me': False
        }, follow=False)
        
        self.assertEqual(response.status_code, 302)
        self.assertIn(response.url, self.success_url)

    def test_invalid_login_returns_form(self):
        """Test that invalid credentials return form with errors"""
        response = self.client.post(self.login_url, {
            'username': self.username,
            'password': 'wrongpassword',
            'remember_me': False
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['form'].is_valid())
        self.assertIn('__all__', response.context['form'].errors)


class SendFriendRequestViewTests(TestCase):
    def setUp(self):
        self.user1 = CustomUser.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = CustomUser.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        self.user3 = CustomUser.objects.create_user(
            username='user3',
            email='user3@example.com',
            password='testpass123'
        )
        self.user_list_url = reverse('user_list')
        self.send_request_url = reverse('send_request', args=[self.user2.id])

    def test_anonymous_user_redirected_to_login(self):
        """Test that anonymous users are redirected to login page"""
        response = self.client.get(self.send_request_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_authenticated_user_can_send_request(self):
        """Test authenticated user can send friend request"""
        self.client.force_login(self.user1)
        response = self.client.get(self.send_request_url)
        
        # Check redirect to user list
        self.assertRedirects(response, self.user_list_url)
        
        # Check friend request was created
        self.assertTrue(FriendRequest.objects.filter(
            from_user=self.user1,
            to_user=self.user2,
            status='pending'
        ).exists())

    def test_duplicate_request_redirects_without_creation(self):
        """Test duplicate friend requests are prevented"""
        self.client.force_login(self.user1)
        
        # First request
        self.client.get(self.send_request_url)
        
        # Second request
        response = self.client.get(self.send_request_url)
        self.assertRedirects(response, self.user_list_url)
        
        # Should only have one request
        self.assertEqual(FriendRequest.objects.filter(
            from_user=self.user1,
            to_user=self.user2
        ).count(), 1)

    def test_cannot_send_request_to_self(self):
        """Test users can't send friend requests to themselves"""
        self.client.force_login(self.user1)
        url = reverse('send_request', args=[self.user1.id])
        response = self.client.get(url)
        
        self.assertRedirects(response, self.user_list_url)
        self.assertFalse(FriendRequest.objects.filter(
            from_user=self.user1,
            to_user=self.user1
        ).exists())

    def test_nonexistent_user_returns_404(self):
        """Test non-existent user ID returns 404"""
        self.client.force_login(self.user1)
        response = self.client.get(reverse('send_request', args=[9999]))
        self.assertEqual(response.status_code, 404)

    def test_can_send_after_previous_rejected_request(self):
        """Test can send new request after previous rejected request"""
        self.client.force_login(self.user1)
        
        # Create and reject first request
        FriendRequest.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            status='rejected'
        )
        
        # Send new request
        response = self.client.get(self.send_request_url)
        self.assertRedirects(response, self.user_list_url)
        
        # Should have two requests (one rejected, one pending)
        self.assertEqual(FriendRequest.objects.filter(
            from_user=self.user1,
            to_user=self.user2
        ).count(), 1)

    def test_multiple_users_can_request_same_user(self):
        """Test multiple users can send requests to the same user"""
        self.client.force_login(self.user1)
        self.client.get(self.send_request_url)
        
        self.client.force_login(self.user3)
        url = reverse('send_request', args=[self.user2.id])
        self.client.get(url)
        
        # Should have two distinct requests
        self.assertEqual(FriendRequest.objects.filter(
            to_user=self.user2
        ).count(), 2)
        self.assertTrue(FriendRequest.objects.filter(
            from_user=self.user1,
            to_user=self.user2
        ).exists())
        self.assertTrue(FriendRequest.objects.filter(
            from_user=self.user3,
            to_user=self.user2
        ).exists())


class RespondRequestViewTests(TestCase):
    def setUp(self):
        self.user1 = CustomUser.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = CustomUser.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        self.user3 = CustomUser.objects.create_user(
            username='user3',
            email='user3@example.com',
            password='testpass123'
        )
        
        self.valid_request = FriendRequest.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            status='pending'
        )
        self.invalid_request = FriendRequest.objects.create(
            from_user=self.user1,
            to_user=self.user3,
            status='pending'
        )
        
        self.home_url = reverse('home')
        self.friend_requests_url = reverse('friend_requests')
        self.accept_url = reverse('respond_request', args=[self.valid_request.id, 'accept'])
        self.reject_url = reverse('respond_request', args=[self.valid_request.id, 'reject'])

    def test_anonymous_user_redirected_to_login(self):
        """Test anonymous users are redirected to login"""
        response = self.client.get(self.accept_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_non_recipient_redirected_to_home(self):
        """Test users who aren't the recipient are redirected"""
        self.client.force_login(self.user3)  # Not the recipient
        response = self.client.get(self.accept_url)
        self.assertIn(response.url, self.home_url)

    def test_accept_request_works(self):
        """Test accepting a friend request works correctly"""
        self.client.force_login(self.user2)  # Valid recipient
        
        response = self.client.get(self.accept_url)
        self.assertRedirects(response, self.friend_requests_url)
        
        # Check request status updated
        self.valid_request.refresh_from_db()
        self.assertEqual(self.valid_request.status, 'accepted')
        
        # Check friends lists updated
        self.assertIn(self.user1, self.user2.friends.all())
        self.assertIn(self.user2, self.user1.friends.all())

    def test_reject_request_works(self):
        """Test rejecting a friend request works correctly"""
        self.client.force_login(self.user2)  # Valid recipient
        
        response = self.client.get(self.reject_url)
        self.assertRedirects(response, self.friend_requests_url)
        
        # Check request status updated
        self.valid_request.refresh_from_db()
        self.assertEqual(self.valid_request.status, 'rejected')
        
        # Check friends lists not updated
        self.assertNotIn(self.user1, self.user2.friends.all())
        self.assertNotIn(self.user2, self.user1.friends.all())

    def test_invalid_action_redirects(self):
        """Test invalid action parameter redirects without changes"""
        self.client.force_login(self.user2)
        invalid_action_url = reverse('respond_request', args=[self.valid_request.id, 'invalid'])
        
        response = self.client.get(invalid_action_url)
        self.assertRedirects(response, self.friend_requests_url)
        
        # Check no changes were made
        self.valid_request.refresh_from_db()
        self.assertEqual(self.valid_request.status, 'pending')
        self.assertNotIn(self.user1, self.user2.friends.all())

    def test_nonexistent_request_returns_404(self):
        """Test non-existent request ID returns 404"""
        self.client.force_login(self.user2)
        response = self.client.get(reverse('respond_request', args=[9999, 'accept']))
        self.assertEqual(response.status_code, 404)

    def test_post_request_works(self):
        """Test POST requests work the same as GET"""
        self.client.force_login(self.user2)
        response = self.client.post(self.accept_url)
        self.assertRedirects(response, self.friend_requests_url)
        
        self.valid_request.refresh_from_db()
        self.assertEqual(self.valid_request.status, 'accepted')

    def test_multiple_accepts_dont_duplicate_friends(self):
        """Test multiple accepts don't duplicate friends"""
        self.client.force_login(self.user2)
        
        # First accept
        self.client.get(self.accept_url)
        friend_count1 = self.user2.friends.count()
        
        # Second accept
        self.client.get(self.accept_url)
        friend_count2 = self.user2.friends.count()
        
        self.assertEqual(friend_count1, friend_count2)
        self.assertEqual(friend_count1, 1)