from django.contrib.auth.models import BaseUserManager
from django.core.exceptions import ValidationError
import re


class CustomUserManager(BaseUserManager):
    """Кастомный менеджер для модели пользователя на основе email"""
    
    def _validate_phone_number(self, phone_number, is_superuser=False):
    # 1️⃣ если телефона нет
        if not phone_number:
            if is_superuser:
                raise ValidationError("Номер телефона обязателен для суперпользователя")
            return  # ← ВАЖНО: обычному пользователю можно без телефона

    # 2️⃣ если телефон есть — проверяем формат
        if not re.match(r'^(?:\+996|0)\d{9}$', phone_number):
            raise ValidationError(
            "Номер телефона должен быть кыргызским: начинаться с +996 или 0 и содержать 9 цифр после."
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
