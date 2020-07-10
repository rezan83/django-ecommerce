from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name="home"),
    path('category/<slug:category_slug>/', views.home, name="home_category"),
    path('product/<int:id>/', views.product, name="product"),
    path('about/', views.about, name="about"),
]
