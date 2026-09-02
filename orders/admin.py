from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'created_at', 'status', 'total_cost', 'delivery_type', 'payment_type']
    list_filter = ['status', 'delivery_type', 'payment_type']
    inlines = [OrderItemInline]
