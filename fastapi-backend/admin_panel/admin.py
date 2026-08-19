from django.contrib import admin

from .models import (
    User,
    Product,
    Cart,
    Order,
    OrderItem,
    Payment,
)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "email",
        "role",
        "created_at",
    )
    search_fields = (
        "name",
        "email",
    )
    list_filter = (
        "role",
    )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "category",
        "price",
        "stock",
        "popularity",
    )
    search_fields = (
        "name",
        "category",
    )
    list_filter = (
        "category",
    )


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "product",
        "quantity",
    )
    search_fields = (
        "user__email",
        "product__name",
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "total_amount",
        "status",
        "created_at",
    )
    search_fields = (
        "user__email",
    )
    list_filter = (
        "status",
    )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "product",
        "quantity",
        "price",
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "amount",
        "payment_method",
        "status",
        "transaction_id",
        "created_at",
    )
    list_filter = (
        "status",
        "payment_method",
    )
    search_fields = (
        "transaction_id",
    )