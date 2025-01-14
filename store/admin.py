from django.contrib import admin
from store import models as store_model


# Tabular Inlines
class GalleryInline(admin.TabularInline):
    model = store_model.Gallery


class VariantInline(admin.TabularInline):
    model = store_model.Variant


class VariantItemInline(admin.TabularInline):
    model = store_model.VariantItem



# Admin Models
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['title', 'icon', 'date']
    list_editable = ['icon']
    prepopulated_fields = {'slug': ('title',)}


class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'stock', 'price', 'regular_price', 'status', 'featured', 'vendor', 'date']  # Исправлено здесь
    search_fields = ['name', 'category__title']
    list_filter = ['status', 'featured', 'category', 'price', 'stock']
    inlines = [GalleryInline, VariantInline]
    prepopulated_fields = {'slug': ('name',)}


class VariantAdmin(admin.ModelAdmin):
    list_display = ['product', 'name']
    search_fields = ['product__name', 'name']
    list_filter = ['product__category']
    inlines = [VariantItemInline]


class VariantItemAdmin(admin.ModelAdmin):
    list_display = ['variant', 'title', 'description']
    search_fields = ['variant__name', 'title']


class GalleryAdmin(admin.ModelAdmin):
    list_display = ['product', 'gallery_id']
    search_fields = ['product__name', 'gallery_id']


class CartAdmin(admin.ModelAdmin):
    list_display = ['cart_id', 'product', 'user', 'qty', 'price', 'total', 'date']
    search_fields = ['cart_id', 'product__name', 'user__username']
    list_filter = ['date', 'product']


class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'vendor', 'discount']
    search_fields = ['code', 'vendor__username']


class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'customer', 'total', 'payment_status', 'order_status', 'payment_method', 'date']
    list_editable = ['payment_status', 'order_status', 'payment_method']
    search_fields = ['order_id', 'customer__username']
    list_filter = ['payment_status', 'order_status']


class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['item_id', 'order', 'product', 'qty', 'price', 'total']
    search_fields = ['item_id', 'order__order_id', 'product__name']
    list_filter = ['order__date']


class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'rating', 'active', 'date']
    search_fields = ['user__username', 'product__name']
    list_filter = ['active', 'rating']


admin.site.register(store_model.Category, CategoryAdmin)
admin.site.register(store_model.Product, ProductAdmin)
admin.site.register(store_model.Variant, VariantAdmin)
admin.site.register(store_model.VariantItem, VariantItemAdmin)
admin.site.register(store_model.Gallery, GalleryAdmin)
admin.site.register(store_model.Cart, CartAdmin)
admin.site.register(store_model.Coupon, CouponAdmin)
admin.site.register(store_model.Order, OrderAdmin)
admin.site.register(store_model.OrderItem, OrderItemAdmin)
admin.site.register(store_model.Review, ReviewAdmin)