from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from modules.models import Module, Grade

CustomUser = get_user_model()


class ModuleModelTests(TestCase):
    def setUp(self):
        # Create a test user
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create some test modules
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

    def test_module_creation(self):
        """Test that a module can be created with required fields"""
        module = Module.objects.create(
            user=self.user,
            name='Chemistry',
            credits=5
        )
        self.assertEqual(module.name, 'Chemistry')
        self.assertEqual(module.credits, 5)
        self.assertEqual(module.user, self.user)

    def test_module_str_representation(self):
        """Test the __str__ method of Module"""
        self.assertEqual(str(self.module1), 'Mathematics')

    def test_overall_grade_with_no_grades(self):
        """Test overall_grade returns None when no grades exist"""
        self.assertIsNone(self.module1.overall_grade())

    def test_overall_grade_with_grades(self):
        """Test overall_grade calculates correctly with grades"""
        # Create grades for module1
        Grade.objects.create(module=self.module1, name='Exam', mark=80, weight=70)
        Grade.objects.create(module=self.module1, name='Coursework', mark=90, weight=30)
        
        # 80*0.7 + 90*0.3 = 56 + 27 = 83
        self.assertEqual(self.module1.overall_grade(), 83.0)

    def test_overall_grade_with_zero_total_weight(self):
        """Test overall_grade returns None when total weight is zero"""
        Grade.objects.create(module=self.module1, name='Test', mark=50, weight=0)
        self.assertIsNone(self.module1.overall_grade())

    def test_module_count_limit(self):
        """Test that a user can't have more than 6 modules"""
        # Create 4 more modules to reach the limit of 6
        Module.objects.create(user=self.user, name='Module3', credits=5)
        Module.objects.create(user=self.user, name='Module4', credits=5)
        Module.objects.create(user=self.user, name='Module5', credits=5)
        Module.objects.create(user=self.user, name='Module6', credits=5)
        
        # Try to create a 7th module
        with self.assertRaises(ValidationError):
            Module.objects.create(user=self.user, name='Module7', credits=5)

    def test_module_count_limit_doesnt_affect_existing(self):
        """Test that existing modules can be saved even when at limit"""
        # Create 4 more modules to reach the limit of 6
        Module.objects.create(user=self.user, name='Module3', credits=5)
        Module.objects.create(user=self.user, name='Module4', credits=5)
        Module.objects.create(user=self.user, name='Module5', credits=5)
        Module.objects.create(user=self.user, name='Module6', credits=5)
        
        # Update an existing module (should work)
        self.module1.name = 'Advanced Mathematics'
        self.module1.save()
        self.assertEqual(self.module1.name, 'Advanced Mathematics')

    def test_module_credits_default_value(self):
        """Test that credits defaults to 0"""
        module = Module.objects.create(user=self.user, name='Default Credits')
        self.assertEqual(module.credits, 0)

    def test_module_user_relation(self):
        """Test the user-module relationship"""
        self.assertEqual(self.user.modules.count(), 2)
        self.assertIn(self.module1, self.user.modules.all())
        self.assertIn(self.module2, self.user.modules.all())

class GradeModelTests(TestCase):
    def setUp(self):
        # Create test user and module
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.module = Module.objects.create(
            user=self.user,
            name='Mathematics',
            credits=15
        )
        
        # Create some initial grades
        self.grade1 = Grade.objects.create(
            module=self.module,
            name='Midterm',
            mark=75.5,
            weight=30.0
        )
        self.grade2 = Grade.objects.create(
            module=self.module,
            name='Assignment',
            mark=82.0,
            weight=20.0
        )

    def test_grade_creation(self):
        """Test basic grade creation"""
        grade = Grade.objects.create(
            module=self.module,
            name='Final Exam',
            mark=85.5,
            weight=50.0
        )
        self.assertEqual(grade.name, 'Final Exam')
        self.assertEqual(grade.mark, 85.5)
        self.assertEqual(grade.weight, 50.0)
        self.assertEqual(grade.module, self.module)

    def test_str_representation(self):
        """Test string representation of grade"""
        self.assertEqual(str(self.grade1), "Assessment: Midterm Mark: 75.5")

    def test_weight_sum_validation(self):
        """Test total weight cannot exceed 100"""
        # Current total weight is 50 (30+20)
        grade = Grade(
            module=self.module,
            name='Extra Credit',
            mark=90.0,
            weight=51.0  # Would make total 101
        )
        with self.assertRaises(ValidationError):
            grade.save()

    def test_negative_weight(self):
        """Test weight cannot be negative"""
        grade = Grade(
            module=self.module,
            name='Invalid Weight',
            mark=50.0,
            weight=-10.0
        )
        with self.assertRaises(ValidationError) as context:
            grade.full_clean()
        self.assertIn('Weight cannot be negative', str(context.exception))
        
        # Also test through save()
        with self.assertRaises(ValidationError):
            grade.save()

    def test_zero_weight(self):
        """Test zero weight is allowed"""
        grade = Grade.objects.create(
            module=self.module,
            name='Practice',
            mark=60.0,
            weight=0.0
        )
        self.assertEqual(grade.weight, 0.0)

    def test_update_grade(self):
        """Test updating a grade"""
        self.grade1.mark = 80.0
        self.grade1.save()
        updated_grade = Grade.objects.get(pk=self.grade1.pk)
        self.assertEqual(updated_grade.mark, 80.0)

    def test_weight_validation_on_update(self):
        """Test weight validation when updating existing grade"""
        self.grade1.weight = 81.0  # Current other weight is 20, total would be 101
        with self.assertRaises(ValidationError):
            self.grade1.save()

    def test_mark_boundaries(self):
        """Test mark must be between 0 and 100"""
        # Test mark < 0
        grade = Grade(
            module=self.module,
            name='Invalid Mark',
            mark=-5.0,
            weight=10.0
        )
        with self.assertRaises(ValidationError):
            grade.full_clean()
            grade.save() 

        # Test mark > 100
        grade = Grade(
            module=self.module,
            name='Invalid Mark',
            mark=110.0,
            weight=10.0
        )
        with self.assertRaises(ValidationError):
            grade.full_clean()
            grade.save()

        for mark in [0.0, 50.0, 100.0]:
            grade = Grade(
                module=self.module,
                name=f'Mark {mark}',
                mark=mark,
                weight=10.0
            )
            try:
                grade.full_clean()
            except ValidationError:
                self.fail(f"Mark {mark} should be valid")

    def test_decimal_precision(self):
        """Test decimal precision handling"""
        grade = Grade.objects.create(
            module=self.module,
            name='Precision Test',
            mark=89.4567,
            weight=10.0
        )
        self.assertAlmostEqual(grade.mark, 89.4567, places=4)

    def test_module_relationship(self):
        """Test grade belongs to module"""
        self.assertEqual(self.grade1.module, self.module)
        self.assertIn(self.grade1, self.module.grades.all())