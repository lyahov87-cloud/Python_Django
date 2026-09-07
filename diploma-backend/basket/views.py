from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from catalog.models import Product
from catalog.serializers import ProductSerializer
from .models import BasketItem


class BasketView(APIView):
    def get(self, request):
        result = []

        if request.user.is_authenticated:
            # Если пользователь вошел — достаем товары из базы данных
            items = request.user.basket_items.select_related('product')
            for item in items:
                product_data = ProductSerializer(item.product).data
                product_data['count'] = item.count
                result.append(product_data)
        else:
            # Если гость — достаем из сессии
            basket = request.session.get('basket', {})
            products = Product.objects.filter(id__in=basket.keys())
            for product in products:
                product_data = ProductSerializer(product).data
                product_data['count'] = basket[str(product.id)]
                result.append(product_data)

        return Response(result)

    def post(self, request):
        product_id = request.data.get('id')
        count = int(request.data.get('count', 1))
        product = get_object_or_404(Product, id=product_id)

        if request.user.is_authenticated:
            # Сохраняем в Базу Данных для авторизованного
            basket_item, created = BasketItem.objects.get_or_create(
                user=request.user,
                product=product,
                defaults={'count': count}
            )
            if not created:
                basket_item.count += count
                basket_item.save()
        else:
            # Сохраняем в сессию для гостя
            basket = request.session.get('basket', {})
            p_id_str = str(product_id)
            if p_id_str in basket:
                basket[p_id_str] += count
            else:
                basket[p_id_str] = count
            request.session['basket'] = basket
            request.session.modified = True

        return self.get(request)

    def delete(self, request):
        product_id = request.data.get('id')
        count = int(request.data.get('count', 1))
        product = get_object_or_404(Product, id=product_id)

        if request.user.is_authenticated:
            # Удаляем/уменьшаем в БД
            try:
                basket_item = BasketItem.objects.get(user=request.user, product=product)
                basket_item.count -= count
                if basket_item.count <= 0:
                    basket_item.delete()
                else:
                    basket_item.save()
            except BasketItem.DoesNotExist:
                pass
        else:
            # Удаляем/уменьшаем в сессии
            basket = request.session.get('basket', {})
            p_id_str = str(product_id)
            if p_id_str in basket:
                basket[p_id_str] -= count
                if basket[basket[p_id_str]] <= 0:
                    del basket[p_id_str]
                request.session['basket'] = basket
                request.session.modified = True

        return self.get(request)
