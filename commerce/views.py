from django.shortcuts import render, get_object_or_404
from .models import Category, Product


def home(request, category_slug=None):

    category = None
    if category_slug != None:
        category = get_object_or_404(Category, slug=category_slug)
        products = Product.objects.all().filter(category=category, available=True)
    else:
        products = Product.objects.all().filter(available=True)

    return render(request, 'home.html', {'category': category,'products': products})


def about(request):
    return render(request, 'about.html')

def product(request, id):
    product = Product.objects.get(pk=id)

    return render(request, 'product.html', {'product': product})
