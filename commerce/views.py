from django.shortcuts import render, get_object_or_404, redirect
from .models import Category, Product, Cart, CartItem
from django.core.exceptions import ObjectDoesNotExist


def home(request, category_slug=None):

    category = None
    if category_slug != None:
        category = get_object_or_404(Category, slug=category_slug)
        products = Product.objects.all().filter(category=category, available=True)
    else:
        products = Product.objects.all().filter(available=True)

    return render(request, 'home.html', {'category': category, 'products': products})


def about(request):
    return render(request, 'about.html')


def product(request, product_id):
    product = Product.objects.get(pk=product_id)

    return render(request, 'product.html', {'product': product})


def _get_cart_session(request):
    cart_session = request.session.session_key or request.session.create()
    return cart_session

def _get_cart(request):
    try:
        cart = Cart.objects.get(cart_session=_get_cart_session(request))
    except Cart.DoesNotExist:
        cart = Cart.objects.create(cart_session=_get_cart_session(request))
        cart.save()
    return cart

def add_to_cart(request, product_id):
    product = Product.objects.get(id=product_id)
    cart = _get_cart(request)
    try:
        cart_item = CartItem.objects.get(
            product=product, cart=cart)
        if cart_item.quantity < cart_item.product.stock:
            cart_item.quantity += 1
        
        cart_item.save()
    except CartItem.DoesNotExist:
        cart_item = CartItem.objects.create(product=product, cart=cart)
        cart_item.save()
    return redirect('cart_detail')


def remove_from_cart(request, product_id):
    product = Product.objects.get(id=product_id)
    cart = _get_cart(request)
    try:
        cart_item = CartItem.objects.get(
            product=product, cart=cart)
        cart_item.delete()
    except CartItem.DoesNotExist:
        pass
    return redirect('cart_detail')


def subtract_from_cart(request, product_id):
    product = Product.objects.get(id=product_id)
    cart = _get_cart(request)
    try:
        cart_item = CartItem.objects.get(
            product=product, cart=cart)
        cart_item.quantity -= 1
        if cart_item.quantity <= 0:
            cart_item.delete()
        else:
            cart_item.save()
    except CartItem.DoesNotExist:
        pass
    return redirect('cart_detail')



def cart_detail(request, total=0, counter=0, cart_items=None, context=None):
    try:
        cart = _get_cart(request)
        cart_items = CartItem.objects.filter(cart=cart, active=True)
        for item in cart_items:
            total+= item.quantity*item.product.price
            counter += item.quantity
        context = {'cart': cart, 'cart_items': cart_items,
                   'total': total, 'counter': counter}
    except ObjectDoesNotExist:
        pass
    return render(request, 'cart.html', context)
