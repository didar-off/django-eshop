from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.db import models
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password

from store import models as store_models
from customer import models as customer_models

@login_required
def dashboard(request):
    orders = store_models.Order.objects.filter(customer=request.user)
    total_spent = store_models.Order.objects.filter(customer=request.user).aggregate(total = models.Sum('total'))['total']
    notis = customer_models.Notification.objects.filter(user=request.user, seen=False)

    context = {
        'orders': orders,
        'total_spent': total_spent,
        'notis': notis,
    }

    return render(request, 'customer/dashboard.html', context)


@login_required
def wishlist(request):
    wishlist = customer_models.Wishlist.objects.filter(user=request.user)

    context = {
        'wishlist': wishlist,
    }

    return render(request, 'customer/wishlist.html', context)


@login_required
def remove_from_wishlist(request, id):
    wishlist = customer_models.Wishlist.objects.get(user=request.user, id=id)
    wishlist.delete()

    messages.success(request, 'Item removed from wishlist')
    return redirect('customer:wishlist')


def add_to_wishlist(request, id):
    if request.user.is_authenticated:
        product = store_models.Product.objects.filter(id=id).first()
        wishlist_exists = customer_models.Wishlist.objects.filter(product=product, user=request.user).first()

        if not wishlist_exists:
            customer_models.Wishlist.objects.create(user=request.user, product=product)
        
        wishlist = customer_models.Wishlist.objects.filter(user=request.user)
        return JsonResponse({'message': 'Item added to wishlist', 'wishlist_count': wishlist.count()})
    else:
        return JsonResponse({'message': 'User is not logged in', 'wishlist_count': '0'})