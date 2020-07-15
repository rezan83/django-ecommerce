from django.db import models
from django.urls import reverse
# from slugify import slugify

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    discription = models.TextField(blank=True)
    image = models.ImageField(upload_to='category', blank=True)
    slug = models.SlugField(max_length=250, unique=True)

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
    # slug = models.SlugField(max_length=250, unique=True)

    class Meta:
        ordering = ('name', )
        verbose_name = "Product"
        verbose_name_plural = "Products"

    def url(self):
        return reverse("product", args=[self.id])

    # def slugify(self):
    #     self.slug = slugify(self.name+str(self.id))

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


