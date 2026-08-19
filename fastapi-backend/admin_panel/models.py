from django.db import models

class User(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=255, unique=True)
    password = models.CharField(max_length=255, null=True, blank=True)
    role = models.CharField(max_length=20)
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "users"

    def __str__(self):
        return f"{self.name} ({self.email})"


class Product(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    category = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
    popularity = models.IntegerField()
    images = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "products"

    def __str__(self):
        return self.name


class Cart(models.Model):
    id = models.IntegerField(primary_key=True)
    user = models.ForeignKey(
        User,
        db_column="user_id",
        on_delete=models.DO_NOTHING
    )
    product = models.ForeignKey(
        Product,
        db_column="product_id",
        on_delete=models.DO_NOTHING
    )
    quantity = models.IntegerField()

    class Meta:
        managed = False
        db_table = "carts"

    def __str__(self):
        return f"{self.user} - {self.product}"


class Order(models.Model):
    id = models.IntegerField(primary_key=True)
    user = models.ForeignKey(
        User,
        db_column="user_id",
        on_delete=models.DO_NOTHING
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    status = models.CharField(max_length=100)
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "orders"

    def __str__(self):
        return f"Order #{self.id}"


class OrderItem(models.Model):
    id = models.IntegerField(primary_key=True)
    order = models.ForeignKey(
        Order,
        db_column="order_id",
        on_delete=models.DO_NOTHING
    )
    product = models.ForeignKey(
        Product,
        db_column="product_id",
        on_delete=models.DO_NOTHING
    )
    quantity = models.IntegerField()
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    class Meta:
        managed = False
        db_table = "order_items"

    def __str__(self):
        return f"Order #{self.order_id} - {self.product}"


class Payment(models.Model):
    id = models.IntegerField(primary_key=True)
    order = models.OneToOneField(
        Order,
        db_column="order_id",
        on_delete=models.DO_NOTHING
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    payment_method = models.CharField(max_length=100)
    status = models.CharField(max_length=100)
    transaction_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "payments"

    def __str__(self):
        return f"Payment #{self.id}"