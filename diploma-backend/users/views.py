from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
import json

from basket.models import BasketItem
from catalog.models import Product
from .serializers import ProfileSerializer



class SignInView(APIView):
    def post(self, request, orders=None):
        # 1. Пробуем достать данные из JSON (через request.data)
        username = None
        password = None

        if isinstance(request.data, dict):
            username = request.data.get('username')
            password = request.data.get('password')

        # 2. Если там пусто, пробуем достать из query-параметров URL (как написано в Swagger)
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
            current_order_id = request.session.get('current_order_id')
            if current_order_id:
                from orders.models import Order
                try:
                    order = Order.objects.get(id=current_order_id)
                    order.user = user  # Переписываем заказ с анонима на вошедшего юзера
                    order.save()
                except Order.DoesNotExist:
                    pass
            session_basket = request.session.get('basket', {})
            if session_basket:
                for product_id, count in session_basket.items():
                    try:
                        product = Product.objects.get(id=product_id)
                        basket_item, created = BasketItem.objects.get_or_create(
                            user=user,
                            product=product,
                            defaults={'count': count}
                        )
                        if not created:
                            basket_item.count += count
                            basket_item.save()
                    except Product.DoesNotExist:
                        pass
                # Очищаем сессионную корзину гостя, так как всё перенесли в БД
                request.session['basket'] = {}
                request.session.modified = True
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


class AvatarUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        profile = request.user.profile
        # Фронтенд присылает файл картинки в ключе 'avatar'
        avatar_file = request.FILES.get('avatar')

        if avatar_file:
            profile.avatar = avatar_file
            profile.save()

            # Возвращаем структуру, которую ждет фронтенд для обновления картинки на экране
            return Response({
                "src": profile.avatar.url,
                "alt": request.user.username
            }, status=status.HTTP_200_OK)

        return Response({"error": "Файл не пришел"}, status=status.HTTP_400_BAD_REQUEST)


class PasswordUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        current_password = request.data.get('currentPassword')
        new_password = request.data.get('newPassword')

        # Проверяем правильность текущего пароля
        if not user.check_password(current_password):
            return Response({"error": "Неверный текущий пароль"}, status=status.HTTP_400_BAD_REQUEST)

        if not new_password:
            return Response({"error": "Новый пароль не может быть пустым"}, status=status.HTTP_400_BAD_REQUEST)

        # Устанавливаем новый пароль и сохраняем сессию, чтобы юзер не «вылетел» из системы
        user.set_password(new_password)
        user.save()
        login(request, user)  # Перезаходим с новым паролем

        return Response(status=status.HTTP_200_OK)
