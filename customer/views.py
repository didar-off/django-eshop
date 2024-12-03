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