from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db import models
from django.db.models.functions import TruncMonth

from store import models as store_models
from vendor import models as vendor_models


def get_monthly_sales():

    monthly_sales = (
        store_models.OrderItem.objects.annotate(month=TruncMonth('date')) # get only month from date field
        .values('month')
        .annotate(order_count = models.Count('id')) # count id
        .order_by('month')
    )

    return monthly_sales


@login_required
def dashboard(request):
    products = store_models.Product.objects.filter(vendor=request.user) #vendor come from product model field
    orders = store_models.Order.objects.filter(vendors=request.user)
    revenue = store_models.OrderItem.objects.filter(vendor=request.user).aggregate(total=models.Sum('total'))['total']
    # {revenue: 100} => {'total': 100 -> grab it and return only amount of total} => 100
    notis = vendor_models.Notification.objects.filter(user=request.user, seen=False)
    reviews = store_models.Review.objects.filter(product__vendor=request.user)
    # we cannot use in filter method produt.vendor instead we can use product__vendor
    monthly_sales = get_monthly_sales()
    rating = store_models.Review.objects.filter(product__vendor=request.user).aggregate(avg=models.Avg('rating'))['avg']

    context = {
        'products': products,
        'orders': orders,
        'revenue': revenue,
        'notis': notis,
        'reviews': reviews,
        'monthly_sales': monthly_sales,
        'rating': rating,
    }

    return render(request, 'vendor/dashboard.html', context)


@login_required
def products(request):
    products = store_models.Product.objects.filter(vendor=request.user)
    
    context = {
        'products': products
    }

    return render(request, 'vendor/products.html', context)