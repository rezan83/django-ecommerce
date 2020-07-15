from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name="home"),
    path('category/<slug:category_slug>/', views.home, name="home_category"),
    path('product/<int:product_id>/', views.product, name="product"),
    path('about/', views.about, name="about"),
    path('cart/add/<int:product_id>/', views.add_to_cart, name="add_to_cart"),
    path('cart/subtract/<int:product_id>/',
         views.subtract_from_cart, name="subtract_from_cart"),
    path('cart/remove/<int:product_id>/',
         views.remove_from_cart, name="remove_from_cart"),
    path('cart/', views.cart_detail, name="cart_detail"),
]
