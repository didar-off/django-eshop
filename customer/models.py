from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from store.models import Product
from userauths.models import User

TYPE = (
    ('New Order', 'New Order'),
    ('Item Shipped', 'Item Shipped'),
    ('Item Delivered', 'Item Delivered'),
)


class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlist')

    class Meta:
        verbose_name = 'Wishlist'
        verbose_name_plural = 'Wishlists'

    def __str__(self):
        if self.product.name:
            return self.product.name
        else:
            return 'Wishlist'
        

class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    full_name = models.CharField(max_length=200, null=True, blank=True, default=None)

    mobile = PhoneNumberField()
    email = models.EmailField()

    country = models.CharField(max_length=100, null=True, blank=True, default=None)
    state = models.CharField(max_length=100, null=True, blank=True, default=None)
    city = models.CharField(max_length=100, null=True, blank=True, default=None)
    
    address = models.CharField(max_length=150, null=True, blank=True, default=None)
    zip_code = models.CharField(max_length=50, null=True, blank=True, default=None)

    class Meta:
        verbose_name = 'Address'
        verbose_name_plural = 'Addresses'

    def __str__(self):
        return self.address
    

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='customer_notification', null=True)
    
    type = models.CharField(max_length=100, choices=TYPE, default=None)
    seen = models.BooleanField(default=False)

    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'

    def __str__(self):
        return self.type

