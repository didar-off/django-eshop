from django.db import models
from shortuuid.django_fields import ShortUUIDField
from django_ckeditor_5.fields import CKEditor5Field
from django.utils.text import slugify
import uuid
import shortuuid
from userauths import models as user_models

# Choices
STATUS = (
    ('Published', 'Published'),
    ('Draft', 'Draft'),
    ('Disabled', 'Disabled'),
)


PAYMENT_STATUS = (
    ('Paid', 'Paid'),
    ('Processing', 'Processing'),
    ('Failed', 'Failed'),
)


PAYMENT_METHOD = (
    ('Cash', 'Cash'),
    ('PayPal', 'PayPal'),
    ('Stripe', 'Stripe'),
    ('Flutterwave', 'Flutterwave'),
    ('Paystack', 'Paystack'),
    ('RazorPay', 'RazorPay'),
)


ORDER_STATUS = (
    ('Pending', 'Pending'),
    ('Processing', 'Processing'),
    ('Shipped', 'Shipped'),
    ('Fulfilled', 'Fulfilled'),
    ('Cancelled', 'Cancelled'),
)


SHIPPING_SERVICE = (
    ('DHL', 'DHL'),
    ('FedX', 'FedX'),
    ('UPS', 'UPS'),
    ('GIG Logistics', 'GIG Logistics'),
)


RATING = (
    (1, '★☆☆☆☆'),
    (2, '★★☆☆☆'),
    (3, '★★★☆☆'),
    (4, '★★★★☆'),
    (5, '★★★★★'),
)


class Category(models.Model):
    """
    Represents a product category in the online store.
    """
    title = models.CharField(max_length=100)

    icon = models.FileField(upload_to='category/icons', null=True, blank=True)
    slug = models.SlugField(unique=True)

    date = models.DateField(auto_now_add=True)
    update = models.DateTimeField(auto_now=True)    

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ['title']

    def __str__(self):
        return self.title
    

class Product(models.Model):
    """
    Represents a product in the online store.
    """
    name = models.CharField(max_length=100)

    image = models.ImageField(upload_to='product/images', default='default-product.jpg', null=True, blank=True)
    description = CKEditor5Field('Description', config_name='extends')
    short_inf = CKEditor5Field('Short Information', config_name='extends')

    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')

    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True, blank=True, verbose_name='Sale Price', help_text='New Price')
    regular_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True, blank=True, verbose_name='Regular Price', help_text='Old Price')

    stock = models.PositiveIntegerField(default=10, null=True, blank=True)
    shipping = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True, blank=True ,verbose_name='Shipping Amount')
    
    status = models.CharField(max_length=50, choices=STATUS, default='Draft')
    featured = models.BooleanField(default=False, verbose_name='Marketplace Featured')

    vendor = models.ForeignKey(user_models.User, on_delete=models.SET_NULL, null=True, blank=True)

    sku = ShortUUIDField(unique=True, max_length=10, length=8, alphabet='1234567890')
    slug = models.SlugField(null=True, blank=True)

    type = models.CharField(max_length=100, default='Organic')

    life = models.CharField(max_length=100, default='10 days')
    date = models.DateTimeField(auto_now_add=True)
    update = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.pk and not self.slug:
            self.slug = slugify(self.name) + '-' + str(shortuuid.uuid().lower()[:2])
        super(Product, self).save(*args, **kwargs)
    
    def average_rating_percentage(self):
        avg = Review.objects.filter(product=self).aggregate(avg_rating=models.Avg('rating'))['avg_rating']
        return (avg * 20) if avg is not None else 0
    
    def average_rating(self):
        avg = Review.objects.filter(product=self).aggregate(avg_rating=models.Avg('rating'))['avg_rating']
        return avg if avg is not None else 0
    
    def reviews(self):
        return Review.objects.filter(product=self)
    
    def gallery(self):
        return Gallery.objects.filter(product=self)
    
    def variants(self):
        return Variant.objects.filter(product=self)
    
    def vendor_orders(self):
        return OrderItem.objects.filter(product=self, vendor=self.vendor)

    def __str__(self):
        return self.name
    

class Variant(models.Model):
    """
    Represents a variant of a product, such as weight or color.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=100, verbose_name='Variant Name', null=True, blank=True)

    def items(self):
        return VariantItem.objects.filter(variant=self)
    
    def __str__(self):
        return self.name
    

class VariantItem(models.Model):
    """
    Represents an item belonging to a specific variant of a product.
    """
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE, related_name='variant_items')
    title = models.CharField(max_length=1000, verbose_name='Variant Item Title', null=True, blank=True)
    description = models.CharField(max_length=1000, verbose_name='Variant Item Description', null=True, blank=True)

    def __str__(self):
        return f'{self.variant.name} - {self.title}'
    

class Gallery(models.Model):
    """
    Represents a gallery of images for a product.
    """
    gallery_id = ShortUUIDField(max_length=10, length=5, alphabet='1234567890')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)
    image = models.ImageField(upload_to='gallery/images', null=True, blank=True)
    
    class Meta:
        verbose_name = "Gallery"
        verbose_name_plural = "Galleries"

    def __str__(self):
        return f'{self.product.name} - image'
    

class Cart(models.Model):
    """
    Represents a shopping cart for a user.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey(user_models.User, on_delete=models.SET_NULL, null=True, blank=True)

    qty = models.PositiveSmallIntegerField(default=0, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True, blank=True)
    sub_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True, blank=True)
    shipping = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True, blank=True)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True, blank=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    # weight = models.CharField(max_length=100, null=True, blank=True)
    # color = models.CharField(max_length=100, null=True, blank=True)
    cart_id = models.CharField(max_length=100, null=True, blank=True)

    date = models.DateTimeField(auto_now_add=True)
    update = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.cart_id} - {self.product.name}'


class Coupon(models.Model):
    """
    Represents a discount coupon that can be applied to orders.
    """
    vendor = models.ForeignKey(user_models.User, on_delete=models.SET_NULL, null=True)
    code = models.CharField(max_length=50)
    discount = models.IntegerField(default=1)

    def __str__(self):
        return self.code
    

class Order(models.Model):
    """
    Represents an order placed by a customer.
    """
    vendors = models.ManyToManyField(user_models.User, blank=True)
    customer = models.ForeignKey(user_models.User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')

    sub_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True, blank=True)
    shipping = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True, blank=True)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True, blank=True)
    service_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True, blank=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True, blank=True)

    payment_status = models.CharField(max_length=100, choices=PAYMENT_STATUS, default='Processing')
    payment_method = models.CharField(max_length=100, choices=PAYMENT_METHOD, default='Cash', null=True, blank=True)
    order_status = models.CharField(max_length=100, choices=ORDER_STATUS, default='Pending')

    initial_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text='The original total before discounts')
    saved = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True, blank=True, help_text='Amount saved with coupon')

    address = models.ForeignKey('customer.Address', on_delete=models.SET_NULL, null=True)
    coupons = models.ManyToManyField(Coupon, blank=True)

    order_id = ShortUUIDField(max_length=10, length=5, alphabet='1234567890')
    payment_id = models.CharField(max_length=100, null=True, blank=True)

    date = models.DateTimeField(auto_now_add=True)
    update = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        ordering = ['-date']

    # Get related order items
    def order_items(self):
        return OrderItem.objects.filter(order=self)

    def __str__(self):
        return f'Order {self.order_id} - {self.customer.email if self.customer else "Customer"}'


class OrderItem(models.Model):
    """
    Representing individual items within an order
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE)

    order_status = models.CharField(max_length=100, choices=ORDER_STATUS, default='Pending')
    shipping_service = models.CharField(max_length=100, choices=SHIPPING_SERVICE, default=None, null=True, blank=True)
    tracking_id = models.CharField(max_length=100, default=None, null=True, blank=True)

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    qty = models.PositiveSmallIntegerField(default=0)
    # color = models.CharField(max_length=100, null=True, blank=True)
    # weight = models.CharField(max_length=100, null=True, blank=True)

    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    sub_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    shipping = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    initial_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text='Grand Total of all amount')

    saved = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True, blank=True, help_text='Saved Amount')
    coupon = models.ManyToManyField(Coupon, blank=True)
    applied_coupon = models.BooleanField(default=False)

    item_id = ShortUUIDField(max_length=10, length=5, alphabet='1234567890')

    vendor = models.ForeignKey(user_models.User, on_delete=models.SET_NULL, null=True, related_name='vendor_order_items')

    date = models.DateTimeField(auto_now_add=True)
    update = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "OrderItem"
        verbose_name_plural = "OrderItems"
        ordering = ['-date']

    def order_id(self):
        return f'{self.order.order_id}'

    def __str__(self):
        return f'{self.item_id} - {self.product.name}'


class Review(models.Model):
    """
    Representing customer reviews for products
    """
    user = models.ForeignKey(user_models.User, on_delete=models.CASCADE)

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews', null=True, blank=True)

    review = models.TextField(null=True, blank=True)
    reply = models.TextField(null=True, blank=True)
    rating = models.IntegerField(choices=RATING, default=None)
    active = models.BooleanField(default=False)
    
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Review"
        verbose_name_plural = "Reviews"

    def __str__(self):
        return f'{self.user.username} reviews on {self.product.name}'

