from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from .managers import CustomUserManager
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации нового пользователя"""
    
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text='Пароль пользователя'
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text='Подтверждение пароля'
    )
    
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phone_number', 'birthday', 'password', 'password2']
        extra_kwargs = {
            'email': {'help_text': 'Email для входа'},
            'first_name': {'help_text': 'Имя пользователя'},
            'last_name': {'help_text': 'Фамилия пользователя'},
            'phone_number': {'required': False, 'help_text': 'Номер телефона (опционально для обычного пользователя)'},
        }
    
    def validate_phone_number(self, value):
        """Валидация номера телефона"""
        manager = CustomUserManager()
        try:
            manager._validate_phone_number(value, is_superuser=False)
        except serializers.ValidationError:
            raise
        return value
    
    def validate(self, data):
        """Проверка что пароли совпадают"""
        if data.get('password') != data.pop('password2'):
            raise serializers.ValidationError({'password': 'Пароли не совпадают'})
        return data
    
    def create(self, validated_data):
        """Создание нового пользователя"""
        user = User.objects.create_user(**validated_data)
        return user


class UserLoginSerializer(serializers.Serializer):
    """Сериализатор для логина пользователя"""
    
    email = serializers.EmailField(
        help_text='Email пользователя'
    )
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text='Пароль пользователя'
    )
    access = serializers.SerializerMethodField()
    refresh = serializers.SerializerMethodField()
    
    def get_access(self, obj):
        """Получить access token"""
        request = self.context.get('request')
        user = request.user if request else None
        if user and user.is_authenticated:
            refresh = RefreshToken.for_user(user)
            return str(refresh.access_token)
        return None
    
    def get_refresh(self, obj):
        """Получить refresh token"""
        request = self.context.get('request')
        user = request.user if request else None
        if user and user.is_authenticated:
            refresh = RefreshToken.for_user(user)
            return str(refresh)
        return None
    
    def validate(self, data):
        """Проверка email и пароля"""
        email = data.get('email')
        password = data.get('password')
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError('Неверный email или пароль')
        
        if not user.check_password(password):
            raise serializers.ValidationError('Неверный email или пароль')
        
        if not user.is_active:
            raise serializers.ValidationError('Пользователь неактивен')
        
        data['user'] = user
        return data


class UserDetailSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения информации о пользователе"""
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'phone_number', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'email': {'read_only': True},
        }


class UserUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления информации о пользователе"""
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number']
        extra_kwargs = {
            'first_name': {'help_text': 'Имя пользователя'},
            'last_name': {'help_text': 'Фамилия пользователя'},
            'phone_number': {'help_text': 'Номер телефона'},
        }


class ChangePasswordSerializer(serializers.Serializer):
    """Сериализатор для смены пароля"""
    
    old_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text='Старый пароль'
    )
    new_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text='Новый пароль'
    )
    new_password2 = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text='Подтверждение нового пароля'
    )
    
    def validate(self, data):
        """Проверка пароля"""
        if data.get('new_password') != data.get('new_password2'):
            raise serializers.ValidationError({'new_password': 'Пароли не совпадают'})
        return data
    
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['birthday'] = str(user.birthday) if user.birthday else None

        return token
    
class OauthCodeSerializer(serializers.Serializer):
    code = serializers.CharField()
