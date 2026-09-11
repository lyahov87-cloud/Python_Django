from basket.models import BasketItem
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Order, OrderItem
from .serializers import OrderSerializer
from catalog.models import Product


class OrdersView(APIView):
    # Разрешаем доступ всем, включая гостей, чтобы не было ошибки 403
    permission_classes = [AllowAny]

    def get(self, request):
        if not request.user.is_authenticated:
            return Response([])
        orders = request.user.orders.all().order_by('-created_at')
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    def post(self, request):
        # Забираем товары из корзины (она работает и для гостей, и для авторизованных)
        basket = request.session.get('basket', {})

        # Если пользователь авторизован, проверим товары в его БД-корзине
        if request.user.is_authenticated:
            db_items = request.user.basket_items.all()
            if db_items.exists():
                basket = {str(item.product.id): item.count for item in db_items}

        if not basket:
            return Response({"error": "Корзина пуста"}, status=status.HTTP_400_BAD_REQUEST)

        # Создаем заказ. Если гость — временно оставляем user=None или привязываем к текущему, если вошел
        if request.user.is_authenticated:
            order = Order.objects.create(user=request.user)
        else:
            # Для гостя находим или создаем временного технического пользователя "guest",
            # либо используем первого попавшегося админа, чтобы не падал ForeignKey,
            # на шаге логина мы перезапишем это поле на реального юзера!
            from django.contrib.auth.models import User
            guest_user, _ = User.objects.get_or_create(username='anonymous_guest', is_active=False)
            order = Order.objects.create(user=guest_user)

        total_cost = 0
        for product_id, count in basket.items():
            try:
                product = Product.objects.get(id=product_id)
                price = product.price
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    price=price,
                    count=count
                )
                total_cost += price * count
            except Product.DoesNotExist:
                pass

        order.total_cost = total_cost
        order.save()

        # Сохраняем ID заказа в сессию гостя, чтобы связать его при авторизации
        request.session['current_order_id'] = order.id
        request.session.modified = True

        return Response({"orderId": order.id}, status=status.HTTP_201_CREATED)


class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        # Получаем данные конкретного заказа для пошаговой формы
        order = get_object_or_404(Order, id=id, user=request.user)
        serializer = OrderSerializer(order)
        return Response(serializer.data)

    def post(self, request, id):
        order = get_object_or_404(Order, id=id, user=request.user)

        order.delivery_type = request.data.get('deliveryType', order.delivery_type)
        order.payment_type = request.data.get('paymentType', order.payment_type)
        order.city = request.data.get('city', order.city)
        order.address = request.data.get('address', order.address)
        order.comment = request.data.get('comment', order.comment)
        order.save()

        # Очищаем корзину
        request.session['basket'] = {}
        request.session.modified = True

        # Возвращаем и id, и orderId, чтобы фронтенд гарантированно не споткнулся
        return Response({"id": order.id, "orderId": order.id}, status=status.HTTP_200_OK)


class PaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        # Находим заказ текущего пользователя
        order = get_object_or_404(Order, id=id, user=request.user)

        # Меняем статус на "Оплачен"
        order.status = 'paid'
        order.save()

        # Уменьшаем остатки товаров на складе
        for item in order.items.all():
            product = item.product
            # Вычитаем купленное количество, но следим, чтобы оно не ушло в минус
            if product.count >= item.count:
                product.count -= item.count
            else:
                product.count = 0  # Если на складе почему-то было меньше, сбрасываем в 0
            product.save()

        # ДОБАВЛЯЕМ ПОЛНУЮ ОЧИСТКУ КОРЗИНЫ В БАЗЕ ДАННЫХ ---
        # Удаляем все товары текущего пользователя из таблицы BasketItem
        BasketItem.objects.filter(user=request.user).delete()

        # На всякий случай очищаем и сессионную корзину гостя
        request.session['basket'] = {}
        request.session.modified = True

        return Response(status=status.HTTP_200_OK)
