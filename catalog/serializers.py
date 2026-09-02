from rest_framework import serializers
from .models import Category, Tag, Product, Review

# --- СЕРИАЛИЗАТОРЫ ДЛЯ ТЕГОВ И КАТЕГОРИЙ ---

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']


class SubCategorySerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'title', 'image']

    def get_image(self, obj):
        if obj.image:
            return {"src": obj.image.url, "alt": obj.title}
        return {"src": "", "alt": "no image"}


class CategorySerializer(serializers.ModelSerializer):
    subcategories = SubCategorySerializer(many=True, read_only=True)
    image = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'title', 'image', 'subcategories']

    def get_image(self, obj):
        if obj.image:
            return {"src": obj.image.url, "alt": obj.title}
        return {"src": "", "alt": "no image"}


# --- СЕРИАЛИЗАТОР ДЛЯ ОТЗЫВОВ ---

class ReviewSerializer(serializers.ModelSerializer):
    date = serializers.DateTimeField(format="%Y-%m-%d %H:%M", read_only=True)
    # Делаем поля гибкими, чтобы отсутствие данных от фронтенда не вызывало ошибку 400
    author = serializers.CharField(required=False, allow_blank=True, default="Аноним")
    email = serializers.EmailField(required=False, allow_blank=True, default="anonymous@example.com")

    class Meta:
        model = Review
        fields = ['author', 'email', 'text', 'rate', 'date']


# --- СЕРИАЛИЗАТОРЫ ДЛЯ ТОВАРОВ ---

# 1. Базовый сериализатор для списков (Каталог, Баннеры, Популярные)
class ProductSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()
    tags = TagSerializer(many=True, read_only=True)
    category = serializers.IntegerField(source='category.id', read_only=True)
    reviews = serializers.IntegerField(default=0, read_only=True)
    rating = serializers.FloatField(default=5.0, read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'category', 'price', 'count', 'date', 'title',
            'description', 'free_delivery', 'images', 'tags', 'reviews', 'rating'
        ]

    def get_images(self, obj):
        if obj.image:
            return [{"src": obj.image.url, "alt": obj.title}]
        return [{"src": "", "alt": obj.title}]


# 2. Расширенный сериализатор для детальной страницы (с выводом списка отзывов)
class ProductFullSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()
    tags = TagSerializer(many=True, read_only=True)
    category = serializers.IntegerField(source='category.id', read_only=True)
    reviews = ReviewSerializer(source='product_reviews', many=True, read_only=True)
    rating = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'category', 'price', 'count', 'date', 'title',
            'description', 'free_delivery', 'images', 'tags', 'reviews', 'rating'
        ]

    def get_images(self, obj):
        if obj.image:
            return [{"src": obj.image.url, "alt": obj.title}]
        return [{"src": "", "alt": obj.title}]

    def get_rating(self, obj):
        reviews = obj.product_reviews.all()
        if reviews.exists():
            return round(sum(r.rate for r in reviews) / reviews.count(), 1)
        return 5.0
