from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Category, Tag, Product
from .serializers import CategorySerializer, TagSerializer, ProductSerializer, ProductFullSerializer, ReviewSerializer
from django.shortcuts import get_object_or_404
from rest_framework import status

class CategoryListView(APIView):
    def get(self, request):
        categories = Category.objects.filter(parent=None)
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)


class TagListView(APIView):
    def get(self, request):
        tags = Tag.objects.all()
        serializer = TagSerializer(tags, many=True)
        return Response(serializer.data)


class CatalogView(APIView):
    def get(self, request):
        # Достаем все товары из базы данных
        products = Product.objects.all()

        # Передаем их в сериализатор
        serializer = ProductSerializer(products, many=True)

        # Фронтенд обязательно ожидает структуру с пагинацией: items, currentPage, lastPage
        return Response({
            "items": serializer.data,
            "currentPage": 1,
            "lastPage": 1
        })

class BannersView(APIView):
    def get(self, request):
        products = Product.objects.filter(is_banner=True)[:3]  # Берем первые 3
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

class PopularProductsView(APIView):
    def get(self, request):
        products = Product.objects.filter(is_popular=True)[:8]  # Топ-8 товаров
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

class LimitedProductsView(APIView):
    def get(self, request):
        products = Product.objects.filter(is_limited=True)[:4]  # Ограниченный тираж
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)


class ProductDetailView(APIView):
    def get(self, request, id):
        product = get_object_or_404(Product, id=id)
        serializer = ProductFullSerializer(product)
        return Response(serializer.data)

    def post(self, request, id):
        # 1. Находим товар, к которому пишется отзыв
        product = get_object_or_404(Product, id=id)

        # 2. Передаем данные из формы фронтенда в сериализатор отзывов
        serializer = ReviewSerializer(data=request.data)

        if serializer.is_valid():
            # 3. Сохраняем отзыв, жестко привязав его к текущему товару
            serializer.save(product=product)

            # 4. Фронтенд ждет в ответ актуальный список ВСЕХ отзывов к этому товару
            all_reviews = product.product_reviews.all()
            response_serializer = ReviewSerializer(all_reviews, many=True)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BasketView(APIView):
    def get(self, request):
        # Достаем корзину из сессии. Если её нет — создаем пустой словарь
        basket = request.session.get('basket', {})

        # Нам нужно достать товары из базы по ID, которые лежат в корзине
        product_ids = basket.keys()
        products = Product.objects.filter(id__in=product_ids)

        result = []
        for product in products:
            # Сериализуем товар через наш стандартный ProductSerializer
            product_data = ProductSerializer(product).data
            # Фронтенд ждет, чтобы внутри каждого товара было поле 'count' с количеством в корзине
            product_data['count'] = basket[str(product.id)]
            result.append(product_data)

        return Response(result)

    def post(self, request):
        product_id = str(request.data.get('id'))
        count = int(request.data.get('count', 1))

        basket = request.session.get('basket', {})

        # Добавляем количество к существующему или создаем новую запись
        if product_id in basket:
            basket[product_id] += count
        else:
            basket[product_id] = count

        # Сохраняем обратно в сессию и помечаем её как измененную
        request.session['basket'] = basket
        request.session.modified = True

        # Возвращаем обновленную корзину (вызываем тот же метод get)
        return self.get(request)

    def delete(self, request):
        product_id = str(request.data.get('id'))
        count = int(request.data.get('count', 1))

        basket = request.session.get('basket', {})

        if product_id in basket:
            # Уменьшаем количество или полностью удаляем ключ
            basket[product_id] -= count
            if basket[product_id] <= 0:
                del basket[product_id]

            request.session['basket'] = basket
            request.session.modified = True

        return self.get(request)
