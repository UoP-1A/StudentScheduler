from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
import tempfile
import os

CustomUser = get_user_model()

class CustomUserModelTests(TestCase):
    def setUp(self):
        # Create a test user
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            profile_bio='Test bio'
        )
    
    def test_user_creation(self):
        """Test that user creation works properly"""
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertEqual(self.user.profile_bio, 'Test bio')
        self.assertTrue(self.user.check_password('testpass123'))
    
    def test_default_profile_picture(self):
        """Test that default profile picture is set correctly"""
        self.assertEqual(
            self.user.profile_picture.name,
            'profile_images/default_user_profile_picture.png'
        )
    
    def test_profile_picture_upload(self):
        """Test that profile picture upload works and gets resized"""
        # Create a test image
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            image = Image.new('RGB', (200, 200), 'red')
            image.save(tmp_file, format='JPEG')
            tmp_file.seek(0)
        
        # Upload the image
        with open(tmp_file.name, 'rb') as img:
            self.user.profile_picture.save(
                'test.jpg',
                SimpleUploadedFile('test.jpg', img.read(), content_type='image/jpeg')
            )
        
        # Check the image was resized
        with Image.open(self.user.profile_picture.path) as img:
            self.assertLessEqual(img.width, 100)
            self.assertLessEqual(img.height, 100)
        
        # Clean up
        os.unlink(tmp_file.name)
        os.unlink(self.user.profile_picture.path)
    
    def test_friends_relationship(self):
        """Test the friends many-to-many relationship"""
        # Create a second user
        user2 = CustomUser.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123',
            profile_bio='Test bio 2'
        )
        
        # Add friend
        self.user.friends.add(user2)
        
        # Check the relationship
        self.assertEqual(self.user.friends.count(), 1)
        self.assertEqual(self.user.friends.first(), user2)
        self.assertEqual(user2.friends.count(), 1)
        self.assertEqual(user2.friends.first(), self.user)
    
    def test_str_representation(self):
        """Test the string representation of the user"""
        self.assertEqual(str(self.user), 'testuser')
    
    def test_profile_bio_can_be_blank(self):
        """Test that a user can be created with a blank profile bio."""
        try:
            user = CustomUser.objects.create_user(
                username='testuser3',
                email='test3@example.com',
                password='testpass123',
                profile_bio=''
            )
            self.assertEqual(user.profile_bio, '')  # Ensure the bio is blank
        except Exception as e:
            self.fail(f"Creating a user with a blank profile bio raised an exception: {e}")

    
    def tearDown(self):
        # Clean up any uploaded files
        if (self.user.profile_picture and 
            self.user.profile_picture.name != 'profile_images/default_user_profile_picture.png' and
            os.path.exists(self.user.profile_picture.path)):
            os.unlink(self.user.profile_picture.path)
    
    def test_username_required(self):
        """Test that username is required"""
        with self.assertRaises(ValueError):
            CustomUser.objects.create_user(
                username='',
                email='test@example.com',
                password='testpass123',
                profile_bio='Test bio'
            )

    def test_invalid_image_upload(self):
        """Test that invalid image files are rejected"""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp_file:
            tmp_file.write(b'This is not an image file')
            tmp_file.seek(0)
        
        with self.assertRaises(Exception): 
            with open(tmp_file.name, 'rb') as file:
                self.user.profile_picture.save(
                    'invalid.txt',
                    SimpleUploadedFile('invalid.txt', file.read(), content_type='text/plain')
                )
        
        os.unlink(tmp_file.name)

    def test_duplicate_username(self):
        """Test that duplicate usernames are rejected"""
        with self.assertRaises(Exception):  # Could be IntegrityError or ValidationError
            CustomUser.objects.create_user(
                username='testuser',  # Same as user created in setUp
                email='test2@example.com',
                password='testpass123',
                profile_bio='Test bio'
            )