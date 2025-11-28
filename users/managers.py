from django.contrib.auth.models import BaseUserManager
from django.core.exceptions import ValidationError
import re


class CustomUserManager(BaseUserManager):
    """Кастомный менеджер для модели пользователя на основе email"""
    
    def _validate_phone_number(self, phone_number, is_superuser=False):
        """
        Валидация номера телефона.
        
        Для суперпользователя phone_number обязателен.
        Для обычного пользователя - опционален.
        
        Формат: +7-XXX-XXX-XX-XX или +7 XXX XXX XX XX и т.д.
        """
        if is_superuser and not phone_number:
            raise ValidationError('Номер телефона обязателен для суперпользователя')
        
        if phone_number:
            # Убираем пробелы, дефисы и скобки для проверки
            clean_phone = re.sub(r'[\s\-()]+', '', phone_number)
            
            # Проверяем что остались только цифры и +
            if not re.match(r'^\+?\d{10,15}$', clean_phone):
                raise ValidationError(
                    'Номер телефона должен содержать от 10 до 15 цифр. '
                    'Допустимые форматы: +7-999-999-99-99 или 89999999999'
                )
    
    def create_user(self, email, password=None, phone_number=None, **extra_fields):
        """
        Создает и сохраняет обычного пользователя с email и паролем
        """
        if not email:
            raise ValueError('Email поле является обязательным')
        
        # Валидация phone_number
        self._validate_phone_number(phone_number, is_superuser=False)
        
        email = self.normalize_email(email)
        user = self.model(email=email, phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, phone_number=None, **extra_fields):
        """
        Создает и сохраняет суперпользователя с email и паролем.
        phone_number ОБЯЗАТЕЛЕН для суперпользователя.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Суперпользователь должен иметь is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Суперпользователь должен иметь is_superuser=True')
        
        # Валидация phone_number для суперпользователя
        self._validate_phone_number(phone_number, is_superuser=True)
        
        return self.create_user(email, password, phone_number, **extra_fields)
