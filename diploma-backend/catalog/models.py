from django.db import models


class Tag(models.Model):
    name = models.CharField(max_length=50, verbose_name="Название")

    def __str__(self):
        return self.name


class Category(models.Model):
    title = models.CharField(max_length=100, verbose_name="Название категории")
    # Самостоятельная связь для подкатегорий (макс. 2 уровня по ТЗ)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories',
        verbose_name="Родительская категория"
    )
    # Поле для иконки категории
    image = models.ImageField(upload_to='categories/', null=True, blank=True, verbose_name="Иконка")

    def __str__(self):
        return self.title


class Product(models.Model):
    title = models.CharField(max_length=255, verbose_name="Название товара")
    description = models.TextField(blank=True, verbose_name="Описание товара")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    count = models.PositiveIntegerField(default=0, verbose_name="Количество на складе")
    date = models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления")
    free_delivery = models.BooleanField(default=False, verbose_name="Бесплатная доставка")

    is_popular = models.BooleanField(default=False, verbose_name="Популярный (Топ)")
    is_limited = models.BooleanField(default=False, verbose_name="Ограниченный тираж")
    is_banner = models.BooleanField(default=False, verbose_name="Отображать в баннерах")

    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products', verbose_name="Категория")
    tags = models.ManyToManyField(Tag, blank=True, related_name='products', verbose_name="Теги")
    image = models.ImageField(upload_to='products/', null=True, blank=True, verbose_name="Изображение товара")

    def __str__(self):
        return self.title

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_reviews', verbose_name="Товар")
    author = models.CharField(max_length=100, verbose_name="Автор")
    email = models.EmailField(verbose_name="Email")
    text = models.TextField(verbose_name="Текст отзыва")
    rate = models.PositiveSmallIntegerField(default=5, verbose_name="Оценка (1-5)")
    date = models.DateTimeField(auto_now_add=True, verbose_name="Дата публикации")

    def __str__(self):
        return f"Отзыв от {self.author} на {self.product.title}"

