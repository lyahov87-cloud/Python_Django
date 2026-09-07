from django.db import models
from django.contrib.auth.models import User
from catalog.models import Product

class BasketItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='basket_items', verbose_name="Пользователь")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Товар")
    count = models.PositiveIntegerField(default=1, verbose_name="Количество")

    class Meta:
        # У одного пользователя не может быть два одинаковых товара отдельными строками
        unique_together = ('user', 'product')

    def __str__(self):
        return f"Корзина {self.user.username}: {self.product.title} x {self.count}"
