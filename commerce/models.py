from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=250, unique=True)
    discription = models.TextField(blank=True)
    image = models.ImageField(upload_to='category', blank=True)

    class Meta:
        ordering = ('name', )
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def url(self):
        return reverse("home_category", args=[self.slug])

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=100, unique=True)
    discription = models.TextField(blank=True)
    image = models.ImageField(upload_to='product', blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    stock = models.IntegerField()
    available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('name', )
        verbose_name = "Product"
        verbose_name_plural = "Products"

    def url(self):
        return reverse("product", args=[self.id])

    def __str__(self):
        return self.name


class Cart(models.Model):
    cart_session = models.CharField(max_length=250, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Cart'
        ordering = ['created_at']

    def __str__(self):
        return self.cart_session


class CartItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    active = models.BooleanField(default=True)

    class Meta:
        db_table = 'CartItem'

    def sub_total(self):
        return self.product.price * self.quantity

    def __str__(self):
        return self.product.name


class Order(models.Model):
    token = models.CharField(max_length=250, blank=True)
    total = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, verbose_name="EUR Total")
    created_at = models.DateTimeField(auto_now_add=True)
    emailAddress = models.EmailField(
        max_length=250, blank=True, verbose_name="Email Address")
    billingName = models.CharField(max_length=250, blank=True)
    billingAddress1 = models.CharField(max_length=250, blank=True)
    billingCity = models.CharField(max_length=250, blank=True)
    billingPostcode = models.CharField(max_length=250, blank=True)
    billingCountry = models.CharField(max_length=250, blank=True)
    shippingName = models.CharField(max_length=250, blank=True)
    shippingAddress1 = models.CharField(max_length=250, blank=True)
    shippingCity = models.CharField(max_length=250, blank=True)
    shippingPostcode = models.CharField(max_length=250, blank=True)
    shippingCountry = models.CharField(max_length=250, blank=True)

    class Meta:
        db_table = 'Order'
        ordering = ['created_at']

    def __str__(self):
        return str(self.id)


class OrderItem(models.Model):
    product = models.CharField(max_length=250)
    price = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, verbose_name="EUR Total")
    quantity = models.IntegerField()
    order = models.ForeignKey(Order, on_delete=models.CASCADE)

    class Meta:
        db_table = 'OrderItem'

    def sub_total(self):
        return self.quantity*self.price

    def __str__(self):
        return self.product

class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    content = models.CharField(max_length=500)
    rate = models.DecimalField(
        max_digits=10, decimal_places=1, blank=True,default=0, verbose_name="rate")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Review'
        ordering = ['created_at']

    def __str__(self):
        return self.content
