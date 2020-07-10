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
    # slug = models.SlugField(max_length=250, unique=True)
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

    # def slugify(self):
    #     self.slug = slugify(self.name+str(self.id))

    def __str__(self):
        return self.name
