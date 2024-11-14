from django.db import models
import uuid
from shortuuid.django_fields import ShortUUIDField
from django_ckeditor_5.fields import CKEditor5Field
from userauths.models import User
from django.utils.text import slugify

NOTIFICATION_TYPE = (
    ('New Order', 'New Order'),
    ('New Review', 'New Review'),
)

PAYOUT_METHOD = (
    ('Cash', 'Cash'),
    ('PayPal', 'PayPal'),
    ('Stripe', 'Stripe'),
    ('Flutterwave', 'Flutterwave'),
    ('Paystack', 'Paystack'),
    ('RazorPay', 'RazorPay'),
)

TYPE = (
    ('New Order', 'New Order'),
    ('Item Shipped', 'Item Shipped'),
    ('Item Delivered', 'Item Delivered'),
)


class Vendor(models.Model):
    vendor_id = ShortUUIDField(unique=True, max_length=10, length=5, alphabet='1234567890')
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)

    image = models.ImageField(upload_to='vendor/images', default='default-vendor.jpg', null=True, blank=True)
    store_name = models.CharField(max_length=100)
    description = CKEditor5Field('Description', config_name='extends')
    country = models.CharField(max_length=100, null=True, blank=True)

    date = models.DateTimeField(auto_now_add=True)
    slug = models.SlugField(null=True, blank=True)

    def __str__(self):
        return self.store_name
    
    def save(self, *args, **kwargs):
        if self.slug == '' or self.slug == None:
            self.slug = slugify(self.store_name)
        super(Vendor, self).save(*args, **kwargs)


class Payout(models.Model):
    payout_id = ShortUUIDField(unique=True, max_length=10, length=5, alphabet='1234567890')

    vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, blank=True)
    item = models.ForeignKey('store.OrderItem', on_delete=models.SET_NULL, null=True, blank=True, related_name='payout')
    amount = models.DecimalField(max_digits=7, decimal_places=2, default=0.00, null=True, blank=True)

    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Payout'
        verbose_name_plural = 'Payouts'
        ordering = ['-date']

    def __str__(self):
        return self.vendor
    

class BankAccount(models.Model):
    vendor = models.OneToOneField(Vendor, on_delete=models.SET_NULL, null=True, blank=True)
    account_type = models.CharField(max_length=50, choices=PAYOUT_METHOD, null=True, blank=True)

    bank_name = models.CharField(max_length=250)
    account_number = models.CharField(max_length=100)
    account_name = models.CharField(max_length=100)
    bank_code = models.CharField(max_length=100, null=True, blank=True)

    stripe_id = models.CharField(max_length=100, null=True, blank=True)
    paypal_address = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        verbose_name = 'BankAccount'
        verbose_name_plural = 'BankAccounts'

    def __str__(self):
        return self.bank_name
    

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vendor_notification')
    type = models.CharField(max_length=100, choices=TYPE, default=None)
    order = models.ForeignKey('store.OrderItem', on_delete=models.CASCADE)
    seen = models.BooleanField(default=False)
    
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'

    def __str__(self):
        return self.type