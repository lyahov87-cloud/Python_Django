from django.urls import path
from .views import (
    CategoryListView, TagListView, CatalogView,
    BannersView, PopularProductsView, LimitedProductsView, ProductDetailView
)

urlpatterns = [
    path('categories', CategoryListView.as_view(), name='categories-list'),
    path('tags', TagListView.as_view(), name='tags-list'),
    path('catalog', CatalogView.as_view(), name='catalog-list'),
    path('banners', BannersView.as_view(), name='banners'),
    path('products/popular', PopularProductsView.as_view(), name='products-popular'),
    path('products/limited', LimitedProductsView.as_view(), name='products-limited'),

    path('product/<int:id>/reviews', ProductDetailView.as_view(), name='product-detail-reviews'),
    path('product/<int:id>', ProductDetailView.as_view(), name='product-detail'),

]
