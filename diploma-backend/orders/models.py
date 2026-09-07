from django.db import models
from django.contrib.auth.models import User
from catalog.models import Product


class Order(models.Model):
    # Статусы заказа для админки и личного кабинета
    STATUS_CHOICES = [
        ('processing', 'Ожидает оплаты / В обработке'),
        ('paid', 'Оплачен'),
        ('delivered', 'Доставлен'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', verbose_name="Покупатель")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    # Данные доставки (заполняются на пошаговой форме)
    delivery_type = models.CharField(max_length=50, default='ordinary', verbose_name="Тип доставки")
    payment_type = models.CharField(max_length=50, default='online', verbose_name="Тип оплаты")

    city = models.CharField(max_length=100, blank=True, verbose_name="Город")
    address = models.TextField(blank=True, verbose_name="Адрес доставки")
    comment = models.TextField(blank=True, verbose_name="Комментарий к заказу")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='processing', verbose_name="Статус заказа")
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Итоговая стоимость")

    def __str__(self):
        return f"Заказ №{self.id} от {self.user.username}"


class OrderItem(models.Model):
    # Промежуточная таблица "Многие-ко-многим" (фиксируем цену на момент покупки)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name="Заказ")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name="Товар")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена при покупке")
    count = models.PositiveIntegerField(default=1, verbose_name="Количество")

    def __str__(self):
        return f"{self.product.title} x {self.count} в заказе №{self.order.id}"
