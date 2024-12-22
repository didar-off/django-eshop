from django.urls import path
from customer import views

app_name = 'customer'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    
    path('wishlist/', views.wishlist, name='wishlist'),
    path('add-to-wishlist/<id>/', views.add_to_wishlist, name='add-to-wishlist'),
    path('remove-from-wishlist/<id>/', views.remove_from_wishlist, name='remove-from-wishlist'),
    
    path('mark-notification-seen/<id>', views.mark_notification_seen, name='mark-notification-seen'),

    path('address-detail/<id>', views.address_detail, name='address-detail'),
    path('address-create/', views.address_create, name='address-create'),
    path('delete-address/<id>/', views.delete_address, name='delete-address'),

    path('update-profile/', views.update_profile, name='update-profile'),
]