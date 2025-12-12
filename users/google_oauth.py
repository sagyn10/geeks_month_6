import requests
from django.utils import timezone
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from users.serializers import OauthCodeSerializer
import os


User = get_user_model()


class GoogleLoginAPIView(CreateAPIView):
    serializer_class = OauthCodeSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        code = serializer.validated_data["code"]

        # 1. Обмениваем code → access_token
        token_url = "https://oauth2.googleapis.com/token"

        data = {
            "code": code,
            "client_id": os.environ.get("GOOGLE_CLIENT_ID"),
            "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET"),
            "redirect_uri":  os.environ.get("GOOGLE_CLIENT_URI"),
            "grant_type": "authorization_code",
        }

        token_response = requests.post(token_url, data=data).json()
        access_token = token_response.get("access_token")

        if not access_token:
            return Response({"error": "Invalid code"}, status=400)

        # 2. Получаем данные пользователя из Google
        user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        user_info = requests.get(
            user_info_url,
            headers={"Authorization": f"Bearer {access_token}"}
        ).json()

        email = user_info.get("email")
        given_name = user_info.get("given_name", "")
        family_name = user_info.get("family_name", "")

        if not email:
            return Response({"error": "Google didn't return email"}, status=400)

        # 3. Создаём / достаём пользователя
        user, created = User.objects.get_or_create(email=email)

        # 4. Заполняем данные под требования задания
        user.first_name = given_name
        user.last_name = family_name
        user.registration_source = "google"
        user.is_active = True
        user.last_login_date = timezone.now()
        user.save()

        # 5. Генерируем JWT
        refresh = RefreshToken.for_user(user)
        refresh["email"] = user.email
        refresh["birthdate"] = str(user.birthdate) if user.birthdate else None

        return Response({
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "registration_source": user.registration_source,
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        })
