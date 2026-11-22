from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal

class Customer(models.Model):
    user = models.OneToOneField(User, null=True, blank=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, null=True)
    email = models.CharField(max_length=200, null=True)
    def __str__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(unique = True, max_length=200)
    created_at = models.DateField(auto_now_add=True)

    class Meta:
        verbose_name_plural = ("Categories")

    def __str__(self):
        return self.name

class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="products")
    name = models.CharField(max_length=200, null=True)
    price = models.DecimalField(max_digits=7,decimal_places=2)
    digital = models.BooleanField(default=False, null=True, blank=True)
    image = models.ImageField(null=True, blank=True) 
    description = models.TextField(null=True, blank=True)
    stock = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name
    @property
    def imageURL(self):
        try:
            url = self.image.url
        except Exception:
                url = ''
        return url

class ProductImage(models.Model):  # ✅ for multiple images
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="products/extra_images/")

    def __str__(self):
        return f"Image for {self.product.name}"

class Variant(models.Model):
    product = models.ForeignKey(Product, related_name="variants", on_delete=models.CASCADE)
    color = models.CharField(max_length=50, null=True, blank=True)
    size = models.CharField(max_length=50, null=True, blank=True)
    price = models.DecimalField(max_digits=7, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)

    def __str__(self):
        parts = []
        if self.color:
            parts.append(self.color)
        if self.size:
            parts.append(self.size)
        label = " / ".join(parts) if parts else "No Variant"
        return f"{self.product.name} - {label}"
        
class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True, db_index=True)
    date_ordered = models.DateTimeField(auto_now_add=True)
    complete = models.BooleanField(default=False, null=True, blank=True)
    transaction_id = models.CharField(max_length=200, null=True)

    def __str__(self):
        return str(self.id)
    
    @property
    def shipping(self):
        shipping = False
        orderitems = self.orderitem_set.all()
        for i in orderitems:
            if i.product.digital == False:
                shipping = True
        return shipping

    @property
    def get_cart_total(self):
        # sourcery skip: comprehension-to-generator, inline-immediately-returned-variable
        orderitem = self.orderitem_set.all()
        total = sum([Decimal(item.get_total) for item in orderitem])
        return total
    @property
    def get_cart_items(self):
        # sourcery skip: comprehension-to-generator, inline-immediately-returned-variable
        orderitem = self.orderitem_set.all()
        total = sum([item.quantity for item in orderitem])
        return total
        
class OrderItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    variant = models.ForeignKey(Variant, on_delete=models.SET_NULL, null=True, blank=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.IntegerField(default=0, null=True, blank=True)
    date_added = models.DateTimeField(auto_now_add=True)

    @property
    def unit_price(self):
        if self.variant:
            return self.variant.price
        return self.product.price

    @property
    def get_total(self):  # sourcery skip: inline-immediately-returned-variable
        return Decimal(self.unit_price) * self.quantity
class ShippingAddress(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True)
    address = models.CharField(max_length=200, null=True)
    city = models.CharField(max_length=200, null=True)
    state = models.CharField(max_length=200, null=True)
    zipcode = models.CharField(max_length=200, null=True)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.address