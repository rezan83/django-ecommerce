from .models import Category, CartItem, Cart
from .views import _get_cart

def cart_items_counter(request):
    counter = 0
    try:
        cart = _get_cart(request)
        cart_items = CartItem.objects.filter(cart=cart, active=True)
        for item in cart_items:
            counter += item.quantity

    except Cart.DoesNotExist:
        pass
    
    return {"counter": counter}

def category_links(request):
    categories = Category.objects.all()
    return {"categories": categories}
