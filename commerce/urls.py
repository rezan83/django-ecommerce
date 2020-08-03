from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name="home"),
    path('search', views.search, name="search"),
    path('category/<slug:category_slug>/', views.home, name="home_category"),
    path('product/<int:product_id>/', views.product, name="product"),
    path('about/', views.about, name="about"),
    path('contact/', views.contact, name="contact"),
    path('cart/add/<int:product_id>/', views.add_to_cart, name="add_to_cart"),
    path('cart/subtract/<int:product_id>/',
         views.subtract_from_cart, name="subtract_from_cart"),
    path('cart/remove/<int:product_id>/',
         views.remove_from_cart, name="remove_from_cart"),
    path('cart/', views.cart_detail, name="cart_detail"),
    path('account/signup/', views.signupView, name="signup"),
    path('account/signin/', views.signinView, name="signin"),
    path('account/signout/', views.signoutView, name="signout"),
    path('account/success/<int:order_id>/', views.success, name="success"),
    path('account/cancel/', views.cancel, name="cancel"),
    path('account/orders_history/', views.orders_history, name="orders_history"),
    path('account/order_detail/<int:order_id>/',
         views.order_detail, name="order_detail"),
]
