from django.contrib import admin

from .models import (
    User,
    Product,
    Order,
    OrderItem,
    Payment,
)


# =========================================================
# USER ADMIN
# =========================================================

@admin.register(User)
class UserAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "name",
        "email",
        "role",
        "is_active",
        "created_at",
    )

    list_filter = (
        "role",
        "is_active",
    )

    search_fields = (
        "name",
        "email",
    )

    list_editable = (
        "role",
        "is_active",
    )

    ordering = (
        "-created_at",
    )


# =========================================================
# PRODUCT ADMIN
# =========================================================

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "name",
        "price",
        "stock",
        "category",
        "popularity",
    )

    list_filter = (
        "category",
    )

    search_fields = (
        "name",
        "category",
        "description",
    )

    list_editable = (
        "price",
        "stock",
        "popularity",
    )

    ordering = (
        "name",
    )


# =========================================================
# ORDER ITEM INLINE
# =========================================================

class OrderItemInline(admin.TabularInline):

    model = OrderItem

    extra = 0

    fields = (
        "product",
        "quantity",
        "price",
    )

    readonly_fields = (
        "product",
        "quantity",
        "price",
    )

    can_delete = False


# =========================================================
# PAYMENT INLINE
# =========================================================

class PaymentInline(admin.StackedInline):

    model = Payment

    extra = 0

    fields = (
        "amount",
        "payment_method",
        "status",
        "transaction_id",
        "created_at",
    )

    readonly_fields = (
        "amount",
        "payment_method",
        "status",
        "transaction_id",
        "created_at",
    )

    can_delete = False


# =========================================================
# ORDER ADMIN
# =========================================================

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    inlines = [
        OrderItemInline,
        PaymentInline,
    ]

    list_display = (
        "id",
        "user",
        "total_amount",
        "status",
        "payment_status",
        "created_at",
    )

    list_filter = (
        "status",
        "payment_status",
    )

    search_fields = (
        "id",
        "user__name",
        "user__email",
    )

    # Admin can update order status directly.
    list_editable = (
        "status",
    )

    readonly_fields = (
        "user",
        "total_amount",
        "payment_status",
        "created_at",
    )

    ordering = (
        "-created_at",
    )


# =========================================================
# ORDER ITEM ADMIN
# =========================================================

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "order",
        "product",
        "quantity",
        "price",
    )

    list_filter = (
        "product",
    )

    search_fields = (
        "order__id",
        "product__name",
    )

    list_editable = (
        "quantity",
        "price",
    )

    ordering = (
        "-id",
    )


# =========================================================
# PAYMENT ADMIN
# =========================================================

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
        "order__id",
    )

    # Payment status can be updated by admin.
    list_editable = (
        "status",
    )

    readonly_fields = (
        "order",
        "amount",
        "payment_method",
        "transaction_id",
        "created_at",
    )

    ordering = (
        "-created_at",
    )
