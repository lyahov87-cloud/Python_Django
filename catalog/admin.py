from django.contrib import admin
from .models import Tag, Category, Product

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
