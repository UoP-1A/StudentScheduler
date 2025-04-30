from django.test import TestCase
from django.contrib.auth import get_user_model

from modules.models import Module, Grade

CustomUser = get_user_model()

class ModulesTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpass123'
        )