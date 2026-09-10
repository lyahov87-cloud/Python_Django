from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Category, Tag, Product
from rest_framework import status
from .serializers import CategorySerializer, TagSerializer, ProductSerializer, ProductFullSerializer, ReviewSerializer


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
        # Оптимизация: select_related подтягивает категорию, prefetch_related подтягивает теги и отзывы
        products = Product.objects.all() \
            .select_related('category') \
            .prefetch_related('tags', 'product_reviews')

        serializer = ProductSerializer(products, many=True)
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

