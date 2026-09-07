from django.urls import path
from .views import OrdersView, OrderDetailView, PaymentView

urlpatterns = [
    path('orders', OrdersView.as_view(), name='orders'),
    path('order/<int:id>', OrderDetailView.as_view(), name='order-detail'),
    path('payment/<int:id>', PaymentView.as_view(), name='payment'),
]
