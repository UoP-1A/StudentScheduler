from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.contrib.messages import get_messages
from ..models import Module, Grade
from ..forms import ModuleCreateForm, GradeCreateForm


CustomUser = get_user_model()

class GetModulesViewTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.module1 = Module.objects.create(
            user=self.user,
            name='Mathematics',
            credits=15
        )
        self.module2 = Module.objects.create(
            user=self.user,
            name='Physics',
            credits=10
        )
        self.url = reverse('modules')

    def test_authenticated_user_with_modules(self):
        """Test view for authenticated user with modules"""
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'modules/modules.html')
        self.assertContains(response, 'Mathematics')
        self.assertContains(response, 'Physics')
        
        # Test forms in context
        self.assertIsInstance(response.context['module_form'], ModuleCreateForm)
        self.assertIsInstance(response.context['grade_form'], GradeCreateForm)
        
        # Test modules in context
        modules = list(response.context['modules'])
        self.assertEqual(len(modules), 2)
        self.assertIn(self.module1, modules)
        self.assertIn(self.module2, modules)

    def test_authenticated_user_without_modules(self):
        """Test view for authenticated user without modules"""
        Module.objects.all().delete()
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['modules']), 0)
        self.assertContains(response, 'No modules available')

    def test_context_data(self):
        """Test all required context data is present"""
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('modules', response.context)
        self.assertIn('module_form', response.context)
        self.assertIn('grade_form', response.context)

    def test_module_queryset(self):
        """Test only requesting user's modules"""
        other_user = CustomUser.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        Module.objects.create(
            user=other_user,
            name='Other Module',
            credits=5
        )
        
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        
        modules = list(response.context['modules'])
        self.assertEqual(len(modules), 2)
        self.assertNotIn('Other Module', [m.name for m in modules])

    def test_unauthenticated_user(self):
        """Test view redirects for unauthenticated users"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            f'/accounts/login/?next={self.url}'
        )

class AddModuleViewTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.url = reverse('add-module')
        self.valid_data = {'name': 'Mathematics', 'credits': '15'}

    def test_valid_form_submission(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, self.valid_data, follow=True)
        self.assertRedirects(response, '/modules/')
        self.assertTrue(Module.objects.filter(name='Mathematics').exists())
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('Module added successfully', str(messages[0]))

    def test_invalid_form_empty_name(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, {'name': '', 'credits': '15'})
        
        # Check form error directly from context
        self.assertEqual(response.status_code, 200)
        form = response.context['module_form']
        self.assertTrue(form.errors)
        self.assertIn('name', form.errors)
        self.assertEqual(form.errors['name'][0], 'This field is required.')

    def test_invalid_form_negative_credits(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, {'name': 'Math', 'credits': '-5'})
        
        # Check form error directly from context
        self.assertEqual(response.status_code, 200)
        form = response.context['module_form']
        self.assertTrue(form.errors)
        self.assertIn('credits', form.errors)
        self.assertEqual(form.errors['credits'][0], 
                        'Ensure this value is greater than or equal to 0.')

    def test_database_validation_error(self):
        for i in range(6):
            Module.objects.create(user=self.user, name=f'Module {i}', credits=5)
            
        self.client.force_login(self.user)
        response = self.client.post(self.url, self.valid_data)
        
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Module.objects.filter(name='Mathematics').exists())
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('Failed to add module', str(messages[0]))

    def test_form_persistence_on_error(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, {'name': 'Math', 'credits': '-5'})
        
        form = response.context['module_form']
        self.assertEqual(form.data['name'], 'Math')
        self.assertEqual(form.data['credits'], '-5')

    def test_unauthenticated_user(self):
        response = self.client.post(self.url, self.valid_data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f'/accounts/login/?next={self.url}')

class AddGradeViewTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.module = Module.objects.create(
            user=self.user,
            name='Mathematics',
            credits=15
        )
        self.url = reverse('add-grade')
        self.valid_data = {
            'module': self.module.id,
            'name': 'Final Exam',
            'mark': '85.5',
            'weight': '50.0'
        }

    def test_valid_form_submission(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, self.valid_data, follow=True)
        
        self.assertRedirects(response, '/modules/')
        self.assertTrue(Grade.objects.filter(name='Final Exam').exists())
        
        # Check for success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('Grade added successfully', str(messages[0]))

    def test_invalid_form_empty_name(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, {
            'module': self.module.id,
            'name': '',
            'mark': '85.5',
            'weight': '50.0'
        })
        
        self.assertEqual(response.status_code, 200)
        form = response.context['grade_form']
        self.assertIn('name', form.errors)
        self.assertEqual(form.errors['name'][0], 'This field is required.')

    def test_invalid_form_mark_out_of_range(self):
        self.client.force_login(self.user)
        
        # Test mark < 0
        response = self.client.post(self.url, {
            'module': self.module.id,
            'name': 'Test',
            'mark': '-5',
            'weight': '50.0'
        })
        form = response.context['grade_form']
        self.assertIn('mark', form.errors)
        
        # Test mark > 100
        response = self.client.post(self.url, {
            'module': self.module.id,
            'name': 'Test',
            'mark': '105',
            'weight': '50.0'
        })
        form = response.context['grade_form']
        self.assertIn('mark', form.errors)

    def test_database_validation_error(self):
        # Create existing grade with weight 60
        Grade.objects.create(
            module=self.module,
            name='Midterm',
            mark=75.0,
            weight=60.0
        )
        
        self.client.force_login(self.user)
        response = self.client.post(self.url, self.valid_data)
        
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Grade.objects.filter(name='Final Exam').exists())
        
        # Check error message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('Failed to add grade', str(messages[0]))

    def test_form_persistence_on_error(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, {
            'module': self.module.id,
            'name': 'Test',
            'mark': '105',  # Invalid mark
            'weight': '50.0'
        })
        
        form = response.context['grade_form']
        self.assertEqual(form.data['name'], 'Test')
        self.assertEqual(form.data['mark'], '105')

class DeleteModuleViewTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username='testuser', password='testpass123')
        self.other_user = CustomUser.objects.create_user(username='otheruser', password='testpass123')
        self.module = Module.objects.create(user=self.user, name='Mathematics', credits=15)
        self.url = reverse('delete-module', args=[self.module.id])

    def test_authenticated_user_can_delete_own_module(self):
        """Test successful deletion by owner via POST"""
        self.client.force_login(self.user)
        response = self.client.post(self.url, follow=True)
        
        self.assertRedirects(response, '/modules/')
        self.assertFalse(Module.objects.filter(id=self.module.id).exists())
        
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('Module deleted successfully', str(messages[0]))

    def test_cannot_delete_nonexistent_module(self):
        """Test handling of invalid module ID"""
        self.client.force_login(self.user)
        invalid_url = reverse('delete-module', args=[999])
        response = self.client.post(invalid_url)
        self.assertEqual(response.status_code, 404)

    def test_cannot_delete_others_module(self):
        """Test authorization check"""
        self.client.force_login(self.other_user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Module.objects.filter(id=self.module.id).exists())

    def test_unauthenticated_user_redirected(self):
        """Test authentication requirement"""
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f'/accounts/login/?next={self.url}')

    def test_get_request_not_allowed(self):
        """Test HTTP method enforcement"""
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

class DeleteGradeViewTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.module = Module.objects.create(
            user=self.user,
            name='Mathematics',
            credits=15
        )
        self.grade = Grade.objects.create(
            module=self.module,
            name='Final Exam',
            mark=85.5,
            weight=50.0
        )
        self.url = reverse('delete-grade', args=[self.grade.id])

    def test_authenticated_user_can_delete_grade(self):
        """Test successful grade deletion"""
        self.client.force_login(self.user)
        response = self.client.post(self.url, follow=True)
        
        self.assertRedirects(response, '/modules/')
        self.assertFalse(Grade.objects.filter(id=self.grade.id).exists())
        
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('Grade deleted successfully', str(messages[0]))

    def test_cannot_delete_nonexistent_grade(self):
        """Test handling of invalid grade ID"""
        self.client.force_login(self.user)
        invalid_url = reverse('delete-grade', args=[999])
        response = self.client.post(invalid_url)
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_user_redirected(self):
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