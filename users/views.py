from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserDetailSerializer,
    UserUpdateSerializer,
    ChangePasswordSerializer,
)
from users.serializers import CustomTokenObtainPairSerializer
from rest_framework.generics import CreateAPIView
from rest_framework import status
from django.db import transaction
import random
import string
from rest_framework.authtoken.models import Token
from .serializers import RegisterValidateSerializer, ConfirmationSerializer
from .utils import set_confirmation_code, pop_confirmation_code
from users.tasks import send_otp_mail

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления пользователями.
    
    Доступные actions:
    - list: Список всех пользователей (только админ)
    - create: Регистрация нового пользователя
    - retrieve: Получить информацию о пользователе
    - update: Обновить информацию о пользователе
    - login: Логин пользователя
    - me: Получить информацию о текущем пользователе
    - change_password: Изменить пароль
    """
    
    queryset = User.objects.all()
    serializer_class = UserDetailSerializer
    
    def get_permissions(self):
        """Определение прав доступа для разных действий"""
        if self.action in ['create', 'login']:
            permission_classes = [AllowAny]
        elif self.action in ['list']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от действия"""
        if self.action == 'create':
            return UserRegistrationSerializer
        elif self.action == 'login':
            return UserLoginSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        elif self.action == 'change_password':
            return ChangePasswordSerializer
        else:
            return UserDetailSerializer
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        """
        Логин пользователя и получение JWT токенов.
        
        Body:
        {
            "email": "user@example.com",
            "password": "password123"
        }
        """
        serializer = self.get_serializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.validated_data.get('user')
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'user': UserDetailSerializer(user).data,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Получить информацию о текущем пользователе"""
        serializer = UserDetailSerializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def change_password(self, request):
        """
        Изменить пароль пользователя.
        
        Body:
        {
            "old_password": "old_password123",
            "new_password": "new_password123",
            "new_password2": "new_password123"
        }
        """
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            
            if not user.check_password(serializer.validated_data.get('old_password')):
                return Response(
                    {'old_password': 'Неверный пароль'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            user.set_password(serializer.validated_data.get('new_password'))
            user.save()
            
            return Response({'detail': 'Пароль успешно изменен'}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def create(self, request, *args, **kwargs):
        """Регистрация нового пользователя"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                UserDetailSerializer(user).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class RegistrationAPIView(CreateAPIView):
    serializer_class = RegisterValidateSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        with transaction.atomic():
            user = User.objects.create_user(
                email=email,
                password=password,
                is_active=False
            )

            code = ''.join(random.choices(string.digits, k=6))

            # Store code in Redis with TTL 5 minutes
            set_confirmation_code(user.id, code, ttl=300)
            
            send_otp_mail.delay(email, code)
        
        return Response(
            status=status.HTTP_201_CREATED,
            data={
                'user_id': user.id,
                'confirmation_code': code
            }
        )


class ConfirmUserAPIView(CreateAPIView):
    serializer_class = ConfirmationSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = ConfirmationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_id = serializer.validated_data['user_id']

        confirmation_code = serializer.validated_data.get('confirmation_code')

        # atomically pop code from redis
        stored = pop_confirmation_code(user_id)
        if not stored:
            return Response({'error': 'Confirmation code expired or not found'}, status=status.HTTP_400_BAD_REQUEST)

        if str(stored) != str(confirmation_code):
            return Response({'error': 'Invalid confirmation code'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            user = User.objects.get(id=user_id)
            user.is_active = True
            user.save()

            token, _ = Token.objects.get_or_create(user=user)

        return Response(
            status=status.HTTP_200_OK,
            data={
                'message': 'User аккаунт успешно активирован',
                'key': token.key
            }
        )

