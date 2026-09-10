from django.contrib import admin
from .models import Tag, Category, Product, Review, ProductImage


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1  # Количество пустых полей по умолчанию для новых картинок


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'parent']
    list_filter = ['parent']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'price', 'count', 'is_popular', 'is_limited', 'is_banner', 'category']
    list_filter = ['category', 'is_popular', 'is_limited', 'is_banner']
    search_fields = ['title']
    inlines = [ProductImageInline]  # Подключили галерею картинок прямо сюда!


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['id', 'product', 'author', 'rate', 'date']
