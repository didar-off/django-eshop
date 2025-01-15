from django.shortcuts import render, redirect
from django.utils.dateformat import DateFormat
from django.http import JsonResponse
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
    products = store_models.Product.objects.filter(vendor=request.user).order_by('date') #vendor come from product model field
    orders = store_models.Order.objects.filter(vendors=request.user)
    revenue = store_models.OrderItem.objects.filter(vendor=request.user).aggregate(total=models.Sum('total'))['total']
    # {revenue: 100} => {'total': 100 -> grab it and return only amount of total} => 100
    notis = vendor_models.Notification.objects.filter(user=request.user, seen=False)
    reviews = store_models.Review.objects.filter(product__vendor=request.user)
    # we cannot use in filter method produt.vendor instead we can use product__vendor
    monthly_sales = get_monthly_sales()
    rating = store_models.Review.objects.filter(product__vendor=request.user).aggregate(avg=models.Avg('rating'))['avg']

    labels = []
    data = []

    for product in products:
        labels.append(product.name)
        data.append(product.stock)

    context = {
        'products': products,
        'orders': orders,
        'revenue': revenue,
        'notis': notis,
        'reviews': reviews,
        'monthly_sales': monthly_sales,
        'rating': rating,
        'labels': labels,
        'data': data,
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
        short_inf = request.POST.get('short_inf')
        description = request.POST.get('description')
        price = request.POST.get('price')
        regular_price = request.POST.get('regular_price')
        shipping = request.POST.get('shipping')
        stock = request.POST.get('stock')

        category = store_models.Category.objects.get(id=category_id)
        product = store_models.Product.objects.create(
            vendor = request.user,
            image = image,
            name = name,
            category = category,
            short_inf = short_inf,
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


@login_required
def update_product(request, id):
    product = store_models.Product.objects.get(vendor=request.user, id=id)
    categories = store_models.Category.objects.all()

    if request.method == 'POST':
        image = request.FILES.get('image')
        name = request.POST.get('name')
        category_id = request.POST.get('category_id') # slect value (category_id) from create-product.html
        short_inf = request.POST.get('short_inf')
        description = request.POST.get('description')
        price = request.POST.get('price')
        regular_price = request.POST.get('regular_price')
        shipping = request.POST.get('shipping')
        stock = request.POST.get('stock')

        category = store_models.Category.objects.get(id=category_id)

        product.name = name
        product.category = category
        product.description = description
        product.short_inf = short_inf
        product.price = price
        product.regular_price = regular_price
        product.shipping = shipping
        product.stock = stock

        if image:
            product.image = image

        product.save()

        variant_ids = request.POST.getlist('variant_id[]')
        variant_title = request.POST.getlist('variant_title[]')

        # variant_ids = ['101', '102', ...]
        # variant_title = ['Small', 'Medium', ...]

        if variant_ids and variant_title:

            for index, variant_id in enumerate(variant_ids):
                variant_name = variant_title[index]

                if variant_id:
                    variant = store_models.Variant.objects.filter(id=variant_id).first()
                    if variant:
                        variant.name = variant_name
                        variant.save()
                else:
                    variant = store_models.Variant.objects.create(product=product, name=variant_name)

                item_ids = request.POST.getlist(f'item_id_{index}[]')
                item_titles = request.POST.getlist(f'item_title_{index}[]')
                item_descriptions = request.POST.getlist(f'item_description_{index}[]')

                """
                    item_ids = ['101', '102', '103']
                    item_titles = ['Small', 'Medium', 'Large']
                    item_description = ['Small size description', 'Medium size description', 'Large size description']
                """

                if item_ids and item_titles and item_descriptions:
                    for j in range(len(item_titles)):

                        item_id = item_ids[j]   # 101
                        item_title = item_titles[j]   # Small
                        item_description = item_descriptions[j]   # Small size description

                        if item_id:
                            variant_item = store_models.VariantItem.objects.filter(id=item_id).first()

                            if variant_item:
                                variant_item.title = item_title
                                variant_item.description = item_description
                                variant_item.save()
                            else:
                                store_models.VariantItem.objects.create(
                                    variant = variant,
                                    title = item_title,
                                    description = item_description
                                )

        for file_key, image_file in request.FILES.items():

            """
                image_1
                image_2
                image_3
                image_4
            """

            if file_key.startwith('image_'):
                store_models.Gallery.objects.create(product = product,image = image_file)

        messages.success(request, 'Product updated successfully')
        return redirect('vendor:update-product', product.id)
    
    context = {
        'product': product,
        'categories': categories,
        'variants': store_models.Variant.objects.filter(product=product),
        'gallery_images': store_models.Gallery.objects.filter(product=product),
    }

    return render(request, 'vendor/update-product.html', context)


@login_required
def delete_variant(request, product_id, variant_id):
    product = store_models.Product.objects.get(id=product_id)
    variant = store_models.Variant.objects.get(id=variant_id, product__vendor=request.user, product=product)
    variant.delete()

    return JsonResponse({'message': 'Variant deleted'})


@login_required
def delete_variant_item(request, variant_id, item_id):
    variant = store_models.Variant.objects.get(id=variant_id)
    item = store_models.VariantItem.objects.get(variant=variant, id=item_id)
    item.delete()

    return JsonResponse({'message': 'Variant Item deleted'})


@login_required
def delete_product_image(request, product_id, image_id):
    product = store_models.Product.objects.get(id=product_id)
    image = store_models.Gallery.objects.get(id=image_id, product=product)
    image.delete()

    return JsonResponse({'message': 'Product Image deleted'})


@login_required
def delete_product(request, product_id):
    product = store_models.Product.objects.get(id=product_id)
    product.delete()

    return redirect('vendor:products')