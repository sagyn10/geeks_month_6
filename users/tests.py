from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .managers import CustomUserManager

User = get_user_model()


class CustomUserManagerTestCase(TestCase):
    """Тесты для CustomUserManager"""
    
    def test_create_user_without_email(self):
        """Проверка что создание пользователя без email выбросит ошибку"""
        with self.assertRaises(ValueError):
            User.objects.create_user(email='', password='test123')
    
    def test_create_user_success(self):
        """Проверка успешного создания пользователя"""
        user = User.objects.create_user(
            email='user@example.com',
            password='test123',
            first_name='John',
            last_name='Doe'
        )
        self.assertEqual(user.email, 'user@example.com')
        self.assertTrue(user.check_password('test123'))
        self.assertFalse(user.is_superuser)
    
    def test_create_superuser_without_phone(self):
        """Проверка что создание суперпользователя без номера телефона выбросит ошибку"""
        with self.assertRaises(ValidationError):
            User.objects.create_superuser(
                email='admin@example.com',
                password='admin123',
                first_name='Admin',
                last_name='User',
                phone_number=None
            )
    
    def test_create_superuser_with_phone(self):
        """Проверка успешного создания суперпользователя с номером телефона"""
        admin = User.objects.create_superuser(
            email='admin@example.com',
            password='admin123',
            first_name='Admin',
            last_name='User',
            phone_number='+7-999-123-45-67'
        )
        self.assertEqual(admin.email, 'admin@example.com')
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_staff)
        self.assertEqual(admin.phone_number, '+7-999-123-45-67')
    
    def test_phone_number_validation_short(self):
        """Проверка валидации коротких номеров телефона"""
        manager = CustomUserManager()
        with self.assertRaises(ValidationError):
            manager._validate_phone_number('123')
    
    def test_phone_number_validation_long(self):
        """Проверка валидации слишком длинных номеров телефона"""
        manager = CustomUserManager()
        with self.assertRaises(ValidationError):
            manager._validate_phone_number('1234567890123456')
    
    def test_phone_number_validation_valid_formats(self):
        """Проверка что валидные форматы номеров принимаются"""
        manager = CustomUserManager()
        # Должны быть валидными эти форматы
        valid_phones = [
            '+7-999-123-45-67',
            '89991234567',
            '+79991234567',
            '+7 999 123 45 67',
            '+7(999)123-45-67'
        ]
        for phone in valid_phones:
            try:
                manager._validate_phone_number(phone, is_superuser=False)
            except ValidationError:
                self.fail(f'Номер {phone} должен быть валидным')


class UserRegistrationAPITestCase(APITestCase):
    """Тесты для API регистрации"""
    
    def setUp(self):
        self.client = APIClient()
        self.register_url = '/api/users/'
    
    def test_user_registration_success(self):
        """Проверка успешной регистрации пользователя"""
        data = {
            'email': 'newuser@example.com',
            'password': 'testpass123',
            'password2': 'testpass123',
            'first_name': 'John',
            'last_name': 'Doe',
            'phone_number': '+7-999-123-45-67'
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['email'], 'newuser@example.com')
    
    def test_user_registration_password_mismatch(self):
        """Проверка регистрации с разными паролями"""
        data = {
            'email': 'newuser@example.com',
            'password': 'testpass123',
            'password2': 'different123',
            'first_name': 'John',
            'last_name': 'Doe'
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_user_registration_duplicate_email(self):
        """Проверка регистрации с существующим email"""
        # Создаем первого пользователя
        User.objects.create_user(
            email='existing@example.com',
            password='test123',
            first_name='First',
            last_name='User'
        )
        # Пытаемся зарегистрировать второго с тем же email
        data = {
            'email': 'existing@example.com',
            'password': 'testpass123',
            'password2': 'testpass123',
            'first_name': 'Second',
            'last_name': 'User'
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserLoginAPITestCase(APITestCase):
    """Тесты для API логина"""
    
    def setUp(self):
        self.client = APIClient()
        self.login_url = '/api/users/login/'
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
    
    def test_user_login_success(self):
        """Проверка успешного логина"""
        data = {
            'email': 'testuser@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['email'], 'testuser@example.com')
    
    def test_user_login_wrong_password(self):
        """Проверка логина с неправильным паролем"""
        data = {
            'email': 'testuser@example.com',
            'password': 'wrongpass123'
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_user_login_nonexistent_email(self):
        """Проверка логина с несуществующим email"""
        data = {
            'email': 'nonexistent@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserProfileAPITestCase(APITestCase):
    """Тесты для API профиля пользователя"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            phone_number='+7-999-123-45-67'
        )
        # Получаем токены
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
    
    def test_get_current_user_info(self):
        """Проверка получения информации о текущем пользователе"""
        response = self.client.get('/api/users/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'testuser@example.com')
        self.assertEqual(response.data['first_name'], 'Test')
    
    def test_update_user_profile(self):
        """Проверка обновления профиля пользователя"""
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'phone_number': '+7-888-999-88-88'
        }
        response = self.client.put(f'/api/users/{self.user.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Updated')

