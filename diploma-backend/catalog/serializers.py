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

    class Meta:
        model = Review
        fields = ['author', 'email', 'text', 'rate', 'date']


# --- СЕРИАЛИЗАТОРЫ ДЛЯ ТОВАРОВ ---

class ProductSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()
    tags = TagSerializer(many=True, read_only=True)
    category = serializers.IntegerField(source='category.id', read_only=True)
    reviews = serializers.IntegerField(default=0, read_only=True)
    rating = serializers.FloatField(default=5.0, read_only=True)

    # Отдаем оба варианта именования для совместимости Swagger + JS
    freeDelivery = serializers.BooleanField(source='free_delivery', default=False)
    free_delivery = serializers.BooleanField(default=False)

    class Meta:
        model = Product
        fields = [
            'id', 'category', 'price', 'count', 'date', 'title',
            'description', 'freeDelivery', 'free_delivery', 'images', 'tags', 'reviews', 'rating'
        ]

    def get_images(self, obj):
        return [{"src": img.image.url, "alt": obj.title} for img in obj.images.all()]


class ProductFullSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()
    tags = TagSerializer(many=True, read_only=True)
    category = serializers.IntegerField(source='category.id', read_only=True)
    reviews = ReviewSerializer(source='product_reviews', many=True, read_only=True)
    rating = serializers.SerializerMethodField()

    # Совместимость полей доставки
    freeDelivery = serializers.BooleanField(source='free_delivery', default=False)
    free_delivery = serializers.BooleanField(default=False)

    # Совместимость описаний по Swagger (строки 554 и 557)
    description = serializers.CharField()
    fullDescription = serializers.CharField(source='description')

    class Meta:
        model = Product
        fields = [
            'id', 'category', 'price', 'count', 'date', 'title',
            'description', 'fullDescription', 'freeDelivery', 'free_delivery',
            'images', 'tags', 'reviews', 'rating'
        ]

    def get_images(self, obj):
        return [{"src": img.image.url, "alt": obj.title} for img in obj.images.all()]

    def get_rating(self, obj):
        reviews = obj.product_reviews.all()
        if reviews.exists():
            return round(sum(r.rate for r in reviews) / reviews.count(), 1)
        return 5.0
