from django.db import models


# =========================================================
# USER
# =========================================================

class User(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    password = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )
    role = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        managed = False
        db_table = "users"

    def __str__(self):
        return self.email


# =========================================================
# PRODUCT
# =========================================================

class Product(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField(
        null=True,
        blank=True,
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )
    stock = models.IntegerField()
    images = models.TextField(
        null=True,
        blank=True,
    )
    category = models.CharField(max_length=255)
    popularity = models.IntegerField()

    class Meta:
        managed = False
        db_table = "products"

    def __str__(self):
        return self.name


# =========================================================
# ORDER
# =========================================================

class Order(models.Model):
    id = models.AutoField(primary_key=True)

    user = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        db_column="user_id",
        related_name="orders",
    )

    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    status = models.CharField(max_length=50)

    payment_status = models.CharField(
        max_length=50,
    )

    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "orders"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.id}"


# =========================================================
# ORDER ITEM
# =========================================================

class OrderItem(models.Model):
    id = models.AutoField(primary_key=True)

    order = models.ForeignKey(
        Order,
        on_delete=models.DO_NOTHING,
        db_column="order_id",
        related_name="items",
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.DO_NOTHING,
        db_column="product_id",
        related_name="order_items",
    )

    quantity = models.IntegerField()

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    class Meta:
        managed = False
        db_table = "order_items"

    def __str__(self):
        return (
            f"Order #{self.order_id} - "
            f"{self.product.name}"
        )


# =========================================================
# PAYMENT
# =========================================================

class Payment(models.Model):
    id = models.AutoField(primary_key=True)

    order = models.OneToOneField(
        Order,
        on_delete=models.DO_NOTHING,
        db_column="order_id",
        related_name="payment",
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    payment_method = models.CharField(
        max_length=50,
    )

    status = models.CharField(
        max_length=50,
    )

    transaction_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "payments"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Payment for Order #{self.order_id}"
