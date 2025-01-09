from django.urls import path
from vendor import views

app_name = "vendor"

urlpatterns = [
    # Vendor Dashboard and Products
    path('dashboard/', views.dashboard, name='dashboard'),
    path('products/', views.products, name='products'),

    # Orders
    path('orders/', views.orders, name='orders'),

    path('order-detail/<order_id>/', views.order_detail, name='order-detail'),
    path('order-item-detail/<order_id>/<item_id>/', views.order_item_detail, name='order-item-detail'),

    path('update-order-status/<order_id>/', views.update_order_status, name='update-order-status'),
    path('update-order-item-status/<order_id>/<item_id>/', views.update_order_item_status, name='update-order-item-status'),

    # Coupons
    path('coupons/', views.coupons, name='coupons'),
    path('update-coupon/<id>/', views.update_coupon, name='update-coupon'),
    path('delete-coupon/<id>/', views.delete_coupon, name='delete-coupon'),
    path('create-coupon/', views.create_coupon, name='create-coupon'),

    # Reviews
    path('reviews/', views.reviews, name='reviews'),
    path('update-reply/', views.update_reply, name='update-reply'),
]
