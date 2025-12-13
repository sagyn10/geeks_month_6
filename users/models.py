from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.validators import EmailValidator
from .managers import CustomUserManager


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """Кастомная модель пользователя с email-аутентификацией"""
    
    email = models.EmailField(
        unique=True,
        validators=[EmailValidator()],
        help_text='Уникальный адрес электронной почты для входа'
    )
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    birthday = models.DateField(null=True, blank=True, help_text='Дата рождения пользователя')
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text='Номер телефона пользователя'
    )
    
    REGISTRATION_CHOICES = [
        ('local', 'Локальная'),
        ('google', 'Google'),
        ('facebook', 'Facebook'),
    ]
    registration_source = models.CharField(
        max_length=50,
        choices=REGISTRATION_CHOICES,
        default='local',
        verbose_name='Источник регистрации'
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'phone_number']
    
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.email
    

class ConfirmationCode(models.Model):
    """Код подтверждения для активации пользователя"""
    user = models.ForeignKey(
        'users.CustomUser', on_delete=models.CASCADE, related_name='confirmation_codes'
    )
    code = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Код подтверждения'
        verbose_name_plural = 'Коды подтверждения'

    def __str__(self) -> str:
        return f"ConfirmationCode(user_id={self.user_id}, code={self.code})"

