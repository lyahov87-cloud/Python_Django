from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
import json
from .models import Profile
from .serializers import ProfileSerializer



class SignInView(APIView):
    def post(self, request):
        # 1. Пробуем достать данные из JSON (через request.data)
        username = None
        password = None

        if isinstance(request.data, dict):
            username = request.data.get('username')
            password = request.data.get('password')

        # 2. Если там пусто, пробуем достать из query-параметров URL (как написано в вашем Swagger)
        if not username:
            username = request.query_params.get('username')
            password = request.query_params.get('password')

        # 3. Если всё ещё пусто, пробуем принудительно распарсить сырое тело запроса (body)
        if not username and request.body:
            try:
                body_data = json.loads(request.body.decode('utf-8'))
                if isinstance(body_data, dict):
                    username = body_data.get('username')
                    password = body_data.get('password')
            except Exception:
                pass

        # Проверяем, удалось ли нам вообще найти данные
        if not username or not password:
            return Response(
                {"error": "Имя пользователя и пароль обязательны"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Аутентификация в Django
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return Response(status=status.HTTP_200_OK)

        return Response(
            {"error": "Неверное имя пользователя или пароль"},
            status=status.HTTP_400_BAD_REQUEST
        )

class SignOutView(APIView):
    def post(self, request):
        logout(request)  # Удаляем сессию пользователя
        return Response(status=status.HTTP_200_OK)


class SignUpView(APIView):
    def post(self, request):
        # Фронтенд может прислать данные строкой JSON в теле запроса
        try:
            if isinstance(request.data, dict):
                data = request.data
            else:
                data = json.loads(request.body)
        except Exception:
            data = request.data

        # Фронтенд обычно передает 'name' (ФИО), 'username' и 'password'
        name = data.get('name')
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return Response({"error": "Заполните обязательные поля"}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists():
            return Response({"error": "Пользователь с таким логином уже существует"},
                            status=status.HTTP_400_BAD_REQUEST)

        # Создаем нового пользователя
        user = User.objects.create_user(username=username, password=password, first_name=name or "")

        login(request, user)

        return Response(status=status.HTTP_200_OK)


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = request.user.profile
        serializer = ProfileSerializer(profile)
        return Response(serializer.data)

    def post(self, request):
        profile = request.user.profile
        user = request.user

        # Разбираем ФИО, которое прислал фронтенд
        user.first_name = request.data.get('fullName', user.first_name)
        user.email = request.data.get('email', user.email)
        user.save()

        # Обновляем телефон в профиле
        profile.phone = request.data.get('phone', profile.phone)
        profile.save()

        serializer = ProfileSerializer(profile)
        return Response(serializer.data)
