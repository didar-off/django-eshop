from django.urls import path
from store import views

app_name = 'store'

urlpatterns = [
    # HomePage
    path('', views.index, name='index'),

    # Product Detail
    path('product-detail/<slug>/', views.product_detail, name='product-detail'),

    # Add To Cart, Cart, Delete Cart Item
    path('add-to-cart/', views.add_to_cart, name='add-to-cart'),
    path('cart/', views.cart, name='cart'),
    path('delete-cart-item/', views.delete_cart_item, name='delete-cart-item'),
]