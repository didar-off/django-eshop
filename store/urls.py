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

    # Create Order, Checkout
    path('create-order/', views.create_order, name='create-order'),
    path('checkout/<order_id>/', views.checkout, name='checkout'),
    path('coupon-apply/<order_id>/', views.coupon_apply, name='coupon-apply'),

    # Payment
    path('paypal-payment-verify/<order_id>/', views.paypal_payment_verify, name='paypal-payment-verify'),
    path('payment-status/<order_id>/', views.payment_status, name='payment-status'),
]