from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password
from django.db import models
from django.db.models.functions import TruncMonth

from django.contrib import messages

from store import models as store_models
from customer import models as customer_models
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


@login_required
def orders(request):
    orders = store_models.Order.objects.filter(vendors=request.user, payment_status='Paid')

    context = {
        'orders': orders
    }

    return render(request, 'vendor/orders.html', context)


@login_required
def order_detail(request, order_id):
    order = store_models.Order.objects.get(vendors=request.user, order_id=order_id, payment_status='Paid')

    context = {
        'order': order
    }

    return render(request, 'vendor/order-detail.html', context)


@login_required
def order_item_detail(request, order_id, item_id):
    order = store_models.Order.objects.get(vendors=request.user, order_id=order_id, payment_status='Paid')
    item = store_models.OrderItem.objects.get(item_id=item_id, order=order)

    context = {
        'order': order, 
        'item': item, 
    }

    return render(request, 'vendor/order-item-detail.html', context)


@login_required
def update_order_status(request, order_id):
    order = store_models.Order.objects.get(vendors=request.user, order_id=order_id, payment_status='Paid')

    if request.method == 'POST':
        order_status = request.POST.get('order_status')
        order.order_status = order_status
        order.save()
        
        messages.success(request, 'Order status updated')
        return redirect('vendor:order-detail', order.order_id)


@login_required
def update_order_item_status(request, order_id, item_id):
    order = store_models.Order.objects.get(vendors=request.user, order_id=order_id, payment_status='Paid')
    item = store_models.OrderItem.objects.get(item_id=item_id, order=order)

    if request.method == 'POST':
        order_status = request.POST.get('order_status')
        shipping_service = request.POST.get('shipping_service')
        tracking_id = request.POST.get('tracking_id')

        item.order_status = order_status
        item.shipping_service = shipping_service
        item.tracking_id = tracking_id
        item.save()
        
        messages.success(request, 'Order status updated')
        return redirect('vendor:order-item-detail', order.order_id, item.item_id)
    
    return redirect('vendor:order-item-detail', order.order_id, item.item_id)


@login_required
def coupons(request):
    coupons = store_models.Coupon.objects.filter(vendor=request.user)

    context = {
        'coupons': coupons
    }

    return render(request, 'vendor/coupons.html', context)


@login_required
def update_coupon(request, id):
    coupon = store_models.Coupon.objects.get(vendor=request.user, id=id)

    if request.method == 'POST':
        code = request.POST.get("coupon_code")
        coupon.code = code
        coupon.save()

    messages.success(request, 'Coupon updated')
    return redirect('vendor:coupons')


@login_required
def delete_coupon(request, id):
    coupon = store_models.Coupon.objects.get(vendor=request.user, id=id)
    coupon.delete()

    messages.success(request, 'Coupon deleted')
    return redirect('vendor:coupons')


@login_required
def create_coupon(request):
    if request.method == 'POST':
        code = request.GET.get('coupon_code')
        discount = request.GET.get('discount')
        store_models.Coupon.objects.create(vendor=request.user, code=code, discount=discount)

    messages.success(request, 'Coupon created')
    return redirect('vendor:coupons')


@login_required
def reviews(request):
    reviews = store_models.Review.objects.filter(product__vendor=request.user)

    rating = request.GET.get('rating')
    date = request.GET.get('date')

    if rating:
        reviews = reviews.filter(rating=rating)

    if date:
        reviews = reviews.order_by(date)

    context = {
        'reviews': reviews,
    }

    return render(request, 'vendor/reviews.html', context)


@login_required
def update_reply(request, id):
    review = store_models.Review.objects.get(id=id)

    if request.method == 'POST':
        reply = request.POST.get('reply')
        review.reply = reply
        review.save()

    messages.success(request, 'Reply added')
    return redirect('vendor:reviews')


@login_required
def notis(request):
    notis = vendor_models.Notification.objects.filter(user=request.user, seen=False)

    context = {
        'notis': notis
    }

    return render(request, 'vendor/notifications.html', context)


@login_required
def mark_notis_seen(request, id):
    noti = vendor_models.Notification.objects.get(user=request.user, id=id)
    noti.seen = True
    noti.save()

    messages.success(request, 'Notification Marked as Seen')
    return redirect('vendor:notifications')


@login_required
def delete_address(request, id):
    address = customer_models.Address.objects.get(user=request.user, id=id)
    address.delete()

    messages.success(request, 'Address was deleted successfully')
    return redirect('customer:dashboard')


@login_required
def profile(request):
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
        return redirect('vendor:profile')

    context = {
        'profile': profile
    }

    return render(request, 'vendor/profile.html', context)


@login_required
def change_password(request):
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_new_password = request.POST.get('confirm_new_password')

        if confirm_new_password != new_password:
            messages.error(request, 'Confirm password and new password Does Not Match')
            return redirect('vendor:change-password')

        if check_password(old_password, request.user.password):
            request.user.set_password(new_password)
            request.user.save()
            messages.success(request, 'Password Changed Successfully')
            return redirect('vendor:dashboard')
        else:
            messages.error(request, 'Old password is Incorrect')
            return redirect('vendor:change-password')
    
    return render(request, 'vendor/change-password.html')


@login_required
def create_product(request):
    categories = store_models.Category.objects.all()

    if request.method == 'POST':
        image = request.FILES.get('image')
        name = request.POST.get('name')
        category_id = request.POST.get('category_id') # slect value (category_id) from create-product.html
        description = request.POST.get('description')
        price = request.POST.get('price')
        regular_price = request.POST.get('regular_price')
        shipping = request.POST.get('shipping')
        stock = request.POST.get('stock')

        category = store_models.Category.objects.get(id=category_id)
        product = store_models.Product.objects.create(
            image = image,
            name = name,
            category = category,
            description = description,
            price = price,
            regular_price = regular_price,
            shipping = shipping,
            stock = stock,
        )

        return redirect('vendor:update-product', product.id)
    
    context = {
        'categories': categories
    }

    return render(request, 'vendor/create-product.html', context)