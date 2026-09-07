from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Order, OrderItem
from .serializers import OrderSerializer
from catalog.models import Product


class OrdersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # История заказов текущего пользователя
        orders = request.user.orders.all().order_by('-created_at')
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    def post(self, request):
        # Создаем заказ на основе товаров из сессионной корзины
        basket = request.session.get('basket', {})
        if not basket:
            return Response({"error": "Корзина пуста"}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Создаем пустой черновик заказа
        order = Order.objects.create(user=request.user)
        total_cost = 0

        # 2. Переносим товары из корзины в OrderItem
        for product_id, count in basket.items():
            product = get_object_or_404(Product, id=product_id)
            price = product.price
            OrderItem.objects.create(
                order=order,
                product=product,
                price=price,
                count=count
            )
            total_cost += price * count

        # 3. Сохраняем финальную стоимость и фиксируем изменения
        order.total_cost = total_cost
        order.save()

        # 4. Фронтенд ждет ответ в формате {"orderId": id}
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

        return Response(status=status.HTTP_200_OK)

