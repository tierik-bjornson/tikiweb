from django.db import models
from user.models import User
from products.models import Book

class Payment(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    fee = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name

class Delivery(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    fee = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    date_created = models.DateTimeField(auto_now_add=True)
    purchase_address = models.TextField()
    delivery_address = models.TextField()
    total_price_product = models.DecimalField(max_digits=10, decimal_places=2)
    fee_payment = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50)
    note = models.TextField(blank=True)
    phone_number = models.CharField(max_length=20)
    full_name = models.CharField(max_length=256)
    fee_delivery = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status_payment = models.CharField(max_length=50)
    status_delivery = models.CharField(max_length=50)
    payment = models.ForeignKey(Payment, on_delete=models.PROTECT)
    delivery = models.ForeignKey(Delivery, on_delete=models.PROTECT)

    def __str__(self):
        return f"Order {self.id} - {self.user.username}"

class OrderDetail(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_details')
    book = models.ForeignKey(Book, on_delete=models.PROTECT)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"OrderDetail {self.id} - Order {self.order.id} - {self.book.name}"
