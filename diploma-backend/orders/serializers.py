from rest_framework import serializers
from .models import Order
from catalog.serializers import ProductSerializer


class OrderSerializer(serializers.ModelSerializer):
    orderId = serializers.IntegerField(source='id', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', format="%Y-%m-%d %H:%M", read_only=True)

    # Данные покупателя
    fullName = serializers.CharField(source='user.first_name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    phone = serializers.CharField(source='user.profile.phone', read_only=True)

    # Поля доставки и стоимости в camelCase через методы
    deliveryType = serializers.SerializerMethodField()
    paymentType = serializers.SerializerMethodField()
    totalCost = serializers.FloatField(source='total_cost', read_only=True)

    # Динамическое плоское поле товаров, как в корзине
    products = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'orderId', 'createdAt', 'fullName', 'email', 'phone',
            'deliveryType', 'paymentType', 'city', 'address',
            'comment', 'status', 'totalCost', 'products'
        ]

    def get_deliveryType(self, obj):
        # Маппинг типов доставки
        types = {
            'ordinary': 'Обычная доставка',
            'express': 'Экспресс-доставка'
        }
        return types.get(obj.delivery_type, obj.delivery_type)

    def get_paymentType(self, obj):
        # Маппинг типов оплаты
        types = {
            'online': 'Онлайн картой',
            'someone': 'Онлайн со случайного счета'
        }
        return types.get(obj.payment_type, obj.payment_type)

    def get_products(self, obj):
        result = []
        for item in obj.items.all():
            product_data = ProductSerializer(item.product).data
            product_data['price'] = float(item.price)
            product_data['count'] = item.count
            result.append(product_data)
        return result
