from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Category, Tag, Product
from rest_framework import status
from .serializers import CategorySerializer, TagSerializer, ProductSerializer, ProductFullSerializer, ReviewSerializer
from django.db.models import Avg, Count


class CategoryListView(APIView):
    def get(self, request):
        # Оптимизация: prefetch_related сразу подтягивает подкатегории, избегая циклов в БД
        categories = Category.objects.filter(parent=None).prefetch_related('subcategories')
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)


class TagListView(APIView):
    def get(self, request):
        tags = Tag.objects.all()
        serializer = TagSerializer(tags, many=True)
        return Response(serializer.data)


class CatalogView(APIView):
    def get(self, request):
        # 1. Аннотируем кверисет средним рейтингом и количеством отзывов для точной сортировки
        queryset = Product.objects.annotate(
            avg_rating=Avg('product_reviews__rate'),
            reviews_count=Count('product_reviews')
        ).select_related('category').prefetch_related('tags', 'product_reviews')

        # 2. Фильтрация по категории
        category_id = request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        # 3. Фильтрация по названию
        name_filter = request.query_params.get('filter[name]')
        if name_filter:
            queryset = queryset.filter(title__icontains=name_filter)

        # 4. Фильтрация по диапазону цен
        min_price = request.query_params.get('filter[minPrice]')
        max_price = request.query_params.get('filter[maxPrice]')
        if min_price:
            queryset = queryset.filter(price__gte=float(min_price))
        if max_price:
            queryset = queryset.filter(price__lte=float(max_price))

        # 5. Фильтрация по бесплатной доставке
        free_delivery = request.query_params.get('filter[freeDelivery]')
        if free_delivery == 'true':
            queryset = queryset.filter(free_delivery=True)

        # 6. Фильтрация по наличию
        available = request.query_params.get('filter[available]')
        if available == 'true':
            queryset = queryset.filter(count__gt=0)

        # 7. Динамическая сортировка по требованиям ТЗ
        sort_field = request.query_params.get('sort', 'date')
        sort_type = request.query_params.get('sortType', 'dec')

        if sort_field == 'price':
            django_sort = 'price'
        elif sort_field == 'rating':
            django_sort = 'avg_rating'  # Сортируем по вычисленному среднему рейтингу
        elif sort_field == 'reviews':
            django_sort = 'reviews_count'  # Сортируем по вычисленному количеству отзывов
        else:
            django_sort = 'id'  # По новизне

        # Применяем направление сортировки (dec - убывание, inc - возрастание)
        if sort_type == 'dec':
            # Нам нужно использовать Coalesce или Nulls Last, но для надежности добавим знак минус
            django_sort = f'-{django_sort}'

        queryset = queryset.order_by(django_sort)

        serializer = ProductSerializer(queryset, many=True)
        return Response({
            "items": serializer.data,
            "currentPage": 1,
            "lastPage": 1
        })


class BannersView(APIView):
    def get(self, request):
        # Добавляем оптимизацию для баннеров
        products = Product.objects.filter(is_banner=True) \
            .select_related('category') \
            .prefetch_related('tags')[:3]
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)


class PopularProductsView(APIView):
    def get(self, request):
        # Добавляем оптимизацию для блока топ-товаров
        products = Product.objects.filter(is_popular=True) \
            .select_related('category') \
            .prefetch_related('tags', 'product_reviews')[:8]
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)


class LimitedProductsView(APIView):
    def get(self, request):
        products = Product.objects.filter(is_limited=True) \
            .select_related('category') \
            .prefetch_related('tags')[:4]
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)


class ProductDetailView(APIView):
    def get(self, request, id):
        product = get_object_or_404(
            Product.objects.select_related('category').prefetch_related('tags', 'product_reviews'),
            id=id
        )
        serializer = ProductFullSerializer(product)
        return Response(serializer.data)

    def post(self, request, id):
        product = get_object_or_404(Product, id=id)
        data = request.data.copy()

        # Если поля пришили пустыми, подставляем дефолты
        if not data.get('author'):
            data['author'] = "Аноним"
        if not data.get('email'):
            data['email'] = "anonymous@example.com"

        serializer = ReviewSerializer(data=data)

        if serializer.is_valid():
            serializer.save(product=product)
            all_reviews = product.product_reviews.all()
            response_serializer = ReviewSerializer(all_reviews, many=True)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
