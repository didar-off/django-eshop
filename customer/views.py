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
    addresses = customer_models.Address.objects.filter(user=request.user)
    profile = request.user.profile

    context = {
        'orders': orders,
        'total_spent': total_spent,
        'notis': notis,
        'addresses': addresses,
        'profile': profile,
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


@login_required
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
    

@login_required
def mark_notification_seen(request, id):
    noti = customer_models.Notification.objects.get(user=request.user, id=id)
    noti.seen = True
    noti.save()

    messages.success(request, 'Notification maked as seen')
    return redirect('customer:dashboard')


@login_required
def address_detail(request, id):
    address = customer_models.Address.objects.get(user=request.user, id=id)

    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        mobile = request.POST.get('mobile')
        email = request.POST.get('email')
        country = request.POST.get('country')
        state = request.POST.get('state')
        city = request.POST.get('city')
        address_location = request.POST.get('address')
        zip_code = request.POST.get('zip_code')

        address.full_name = full_name
        address.mobile = mobile
        address.email = email
        address.country = country
        address.state = state
        address.city = city
        address.address = address_location
        address.zip_code = zip_code
        address.save()

        messages.success(request, 'Address was updated successfully')
        return redirect('customer:dashboard')
    
    context = {
        'address': address
    }

    return render(request, 'customer/address-detail.html', context)


@login_required
def address_create(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        mobile = request.POST.get('mobile')
        email = request.POST.get('email')
        country = request.POST.get('country')
        state = request.POST.get('state')
        city = request.POST.get('city')
        address_location = request.POST.get('address')
        zip_code = request.POST.get('zip_code')

        customer_models.Address.objects.create(
            user = request.user,
            full_name = full_name,
            mobile = mobile,
            email = email,
            country = country,
            state = state,
            city = city,
            address = address_location,
            zip_code = zip_code,
        )

        messages.success(request, 'Address was created successfully')
        return redirect('customer:dashboard')

    return render(request, 'customer/address-create.html')


@login_required
def delete_address(request, id):
    address = customer_models.Address.objects.get(user=request.user, id=id)
    address.delete()

    messages.success(request, 'Address was deleted successfully')
    return redirect('customer:dashboard')


@login_required
def update_profile(request):
    profile = request.user.profile

    if request.method == 'POST':
        image = request.FILES.get('image')
        full_name = request.POST.get('full_name')
        mobile = request.POST.get('mobile')

        if image:
            profile.image = image

        profile.full_name = full_name
        profile.mobile = mobile
        profile.save()

        messages.success(request, 'Profile Updated Successfully')
        return redirect('customer:dashboard')

    return redirect('customer:dashboard')


@login_required
def change_password(request):
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_new_password = request.POST.get('confirm_new_password')

        if confirm_new_password != new_password:
            messages.error(request, 'Confirm password and new password Does Not Match')
            return redirect('customer:change-password')

        if check_password(old_password, request.user.password):
            request.user.set_password(new_password)
            request.user.save()
            messages.success(request, 'Password Changed Successfully')
            return redirect('customer:dashboard')
        else:
            messages.error(request, 'Old password is Incorrect')
            return redirect('customer:change-password')
    
    
    return redirect('customer:dashboard')