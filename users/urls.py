from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet
from rest_framework_simplejwt.views import (
    # TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from users.views import CustomTokenObtainPairView
from users.google_oauth import GoogleLoginAPIView
from .views import RegistrationAPIView, ConfirmUserAPIView
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
    path('jwt/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('jwt/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('jwt/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    path('google-login/', GoogleLoginAPIView.as_view())
,
    path('auth/register/', RegistrationAPIView.as_view(), name='register'),
    path('auth/confirm/', ConfirmUserAPIView.as_view(), name='confirm'),
]


   
 
    