from django.shortcuts import render, redirect
from django.http import JsonResponse
import razorpay.errors

from store import models as store_models
from customer import models as customer_models
from vendor import models as vendor_models

from decimal import Decimal
from django.db.models import Q, Avg, Sum

from django.contrib import messages
from django.conf import settings

import requests
import stripe
import razorpay

from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from plugins.tax_calculation import tax_calculation
from plugins.service_fee import calculate_service_fee
from plugins.exchange_rate import convert_usd_inr, convert_usd_kobo, convert_usd_ngn


stripe.api_key = settings.STRIPE_SECRET_KEY
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


def index(request):
    products = store_models.Product.objects.filter(status='Published')
    categories = store_models.Category.objects.all()

    context = {
        'products': products,
        'categories': categories,
    }

    return render(request, 'store/index.html', context)


def product_detail(request, slug):
    product = store_models.Product.objects.get(status='Published', slug=slug)
    related_product = store_models.Product.objects.filter(category=product.category, status='Published').exclude(id=product.id)

    # variant_items = []
    # for variant in product.variants():
    #     for item in variant.variant_items.all():
    #         if item.title == 'Weight' or item.title == 'weight' or item.title =='Size' or item.title == 'size':
    #             item.description_list = item.description.split(',')
    #             variant_items.append(item)

    context = {
        'product': product,
        'related_product': related_product,
        # 'variant_items': variant_items,
    }

    return render(request, 'store/product-detail.html', context)


def add_to_cart(request):
    id = request.GET.get('id')
    qty = request.GET.get('qty')
    cart_id = request.GET.get('cart_id')

    request.session['cart_id'] = cart_id

    if not id or not qty or not cart_id:
        return JsonResponse({'error': 'No id, qty or cart_id'}, status=400)
    
    try:
        product = store_models.Product.objects.get(status='Published', id=id)
    except store_models.Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=400)
    
    existing_cart_items = store_models.Cart.objects.filter(cart_id=cart_id, product=product).first()
    if int(qty) > product.stock:
        return JsonResponse({'error': 'Qty exceed current stock amount'}, status=404)
    
    if not existing_cart_items:
        cart = store_models.Cart()
        cart.product = product
        cart.qty = qty
        cart.price = product.price
        cart.sub_total = Decimal(product.price) * Decimal(qty)
        cart.shipping = Decimal(product.shipping)
        cart.total = cart.sub_total + cart.shipping
        cart.user = request.user if request.user.is_authenticated else None
        cart.cart_id = cart_id
        cart.save()

        message = 'Item added to cart'
    else:
        existing_cart_items.product = product
        existing_cart_items.qty = qty
        existing_cart_items.price = product.price
        existing_cart_items.sub_total = Decimal(product.price) * Decimal(qty)
        existing_cart_items.shipping = Decimal(product.shipping)
        existing_cart_items.total = existing_cart_items.sub_total + existing_cart_items.shipping
        existing_cart_items.user = request.user if request.user.is_authenticated else None
        existing_cart_items.cart_id = cart_id
        existing_cart_items.save()

        message = 'Cart Updated'

    total_cart_items = store_models.Cart.objects.filter(Q(cart_id=cart_id))
    cart_sub_total = store_models.Cart.objects.filter(cart_id=cart_id).aggregate(sub_total=Sum('sub_total'))['sub_total']

    return JsonResponse({
        'message': message,
        'total_cart_items': total_cart_items.count(),
        'cart_sub_total': '{:,.2f}'.format(cart_sub_total),
        'item_sub_total': '{:,.2f}'.format(existing_cart_items.sub_total) if existing_cart_items else '{:,.2f}'.format(cart.sub_total),
    })


def cart(request):
    if 'cart_id' in request.session:
        cart_id = request.session['cart_id']
    else:
        cart_id = None

    items = store_models.Cart.objects.filter(Q(cart_id=cart_id) | Q(user=request.user) if request.user.is_authenticated else Q(cart_id=cart_id))
    cart_sub_total = store_models.Cart.objects.filter(Q(cart_id=cart_id) | Q(user=request.user) if request.user.is_authenticated else Q(cart_id=cart_id)).aggregate(sub_total = Sum('sub_total'))['sub_total']

    try:
        addresses = customer_models.Address.objects.filter(user=request.user)
    except:
        addresses = None

    if not items:
        messages.warning(request, 'No items in cart')
        return redirect('store:index')
    
    context = {
        'items': items,
        'cart_sub_total': cart_sub_total,
        'addresses': addresses,
    }

    return render(request, 'store/cart.html', context)


def delete_cart_item(request):
    id = request.GET.get('id')
    item_id = request.GET.get('item')
    cart_id = request.GET.get('cart_id')

    print('Product ID: ', id)
    print('Item ID: ', item_id)
    print('Cart ID: ', cart_id)

    if not id or not item_id or not cart_id:
        return JsonResponse({'error': 'Item or Product Id not found'}, status=400)
    
    try:
        product = store_models.Product.objects.get(status='Published', id=id)
    except store_models.Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)
    
    item = store_models.Cart.objects.get(product=product, id=item_id)
    item.delete()

    total_cart_items = store_models.Cart.objects.filter(Q(cart_id=cart_id) | Q(user=request.user))
    cart_sub_total = store_models.Cart.objects.filter(Q(cart_id=cart_id) | Q(user=request.user)).aggregate(sub_total = Sum('sub_total'))['sub_total']

    return JsonResponse({
        'message': 'Item Deleted',
        'total_cart_items' : total_cart_items.count(),
        'cart_sub_total': '{:,.2f}'.format(cart_sub_total) if cart_sub_total else 0.00
    })


def create_order(request):
    if request.method == 'POST':
        address_id = request.POST.get('address')

        if not address_id:
            messages.warning(request, 'Please create or select an address to continue')
            return redirect('store:cart')
        
        address = customer_models.Address.objects.filter(user=request.user, id=address_id).first()

        if 'cart_id' in request.session:
            cart_id = request.session['cart_id']
        else:
            cart_id = None
        
        items = store_models.Cart.objects.filter(Q(cart_id=cart_id) | Q(user=request.user) if request.user.is_authenticated else Q(cart_id=cart_id))
        cart_sub_total = store_models.Cart.objects.filter(Q(cart_id=cart_id) | Q(user=request.user) if request.user.is_authenticated else Q(cart_id=cart_id)).aggregate(sub_total = Sum('sub_total'))['sub_total']
        cart_shipping_total = store_models.Cart.objects.filter(Q(cart_id=cart_id) | Q(user=request.user) if request.user.is_authenticated else Q(cart_id=cart_id)).aggregate(shipping = Sum('shipping'))['shipping']

        order = store_models.Order()
        order.sub_total = cart_sub_total
        order.customer = request.user
        order.address = address
        order.shipping = cart_shipping_total
        order.tax = tax_calculation(address.country, cart_sub_total)
        order.total = order.sub_total + order.shipping + Decimal(order.tax)
        order.service_fee = calculate_service_fee(order.total)
        order.total += order.service_fee
        order.initial_total = order.total
        order.save()

        for i in items:
            store_models.OrderItem.objects.create(
                order = order,
                product = i.product,
                qty = i.qty,
                price = i.price,
                sub_total = i.sub_total,
                shipping = i.shipping,
                tax = tax_calculation(address.country, i.sub_total),
                total = i.total,
                initial_total = i.total,
                vendor = i.product.vendor,
            )

            order.vendors.add(i.product.vendor)

    return redirect('store:checkout', order.order_id)


def clear_cart_items(request):
    try:
        cart_id = request.session['cart_id']
        store_models.Cart.objects.filter(cart_id=cart_id).delete()
    except:
        pass

    return


def checkout(request, order_id):
    order = store_models.Order.objects.get(order_id=order_id)

    amount_in_inr = convert_usd_inr(order.total)
    amount_in_kobo = convert_usd_kobo(order.total)
    amount_in_ngn = convert_usd_ngn(order.total)

    try:
        razorpay_order = razorpay_client.order.create({
            'amount': int(amount_in_inr),
            'currency': 'INR',
            'payment_capture': '1'
        })
    except:
        razorpay_order = None


    context = {
        'order': order,
        'razorpay_order_id': razorpay_order['id'] if razorpay_order else None,
        'amount_in_inr': amount_in_inr,
        'amount_in_kobo': amount_in_kobo,
        'amount_in_ngn': amount_in_ngn,
        'paypal_client_id': settings.PAYPAL_CLIENT_ID,
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
        'paystack_public_key': settings.PAYSTACK_PUBLIC_KEY,
        'flutterwave_public_key': settings.FLUTTERWAVE_PUBLIC_KEY,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID
    }

    return render(request, 'store/checkout.html', context)


def coupon_apply(request, order_id):
    try:
        order = store_models.Order.objects.get(order_id=order_id)
        order_items = store_models.OrderItem.objects.filter(order=order)
    except store_models.Order.DoesNotExist:
        return redirect('store:cart')
    
    if request.method == 'POST':
        coupon_code = request.POST.get('coupon_code')

        if not coupon_code:
            messages.error(request, 'No coupon entered')
            return redirect('store:checkout', order.order_id)
        
        try:
            coupon = store_models.Coupon.objects.get(code=coupon_code)
        except store_models.Coupon.DoesNotExist:
            messages.error(request, 'Coupon does not exist')
            return redirect('store:checkout', order.order_id)
        
        if coupon in order.coupons.all():
            messages.error(request, 'Coupon already activated')
            return redirect('store:checkout', order.order_id)
        else:
            total_discount = 0
            
            for item in order_items:
                if coupon.vendor == item.product.vendor and coupon not in item.coupon.all():
                    item_discount = item.total * coupon.discount / 100
                    total_discount += item_discount

                    item.coupon.add(coupon)
                    item.total -= item_discount
                    item.saved += item_discount
                    item.save()
                
            if total_discount > 0:
                order.coupons.add(coupon)
                order.total -= total_discount
                order.sub_total -= total_discount
                order.saved += total_discount
                order.save()
    
        messages.success(request, 'Coupon activated')
        return redirect('store:checkout', order.order_id)
    

def get_paypal_access_token():
    token_url = 'https://api.sandbox.paypal.com/v1/oauth2/token'
    data = {'grant_type': 'client_credentials'}
    auth = (settings.PAYPAL_CLIENT_ID, settings.PAYPAL_SECRET_ID)
    response = requests.post(token_url, data=data, auth=auth)

    if response.status_code == 200:
        return response.json()['access_token']
    else:
        raise Exception(f'Failed to get access token from PayPal. Status code: {response.status_code}')
    

def paypal_payment_verify(request, order_id):
    order = store_models.Order.objects.get(order_id=order_id)
    
    transaction_id = request.GET.get('transaction_id')
    paypal_api_url = f'https://api-m.sandbox.paypal.com/v2/checkout/orders/{transaction_id}'

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {get_paypal_access_token()}'

    }

    print(get_paypal_access_token())

    response = requests.get(paypal_api_url, headers=headers)

    if response.status_code == 200:
        paypal_order_data = response.json()
        paypal_payment_status = paypal_order_data['status']
        payment_method = 'PayPal'
        
        if paypal_payment_status == 'COMPLETED':
            if order.payment_status == 'Processing':
                order.payment_status = 'Paid'
                order.payment_method = 'PayPal'
                order.save()
                clear_cart_items(request)
                return redirect(f'/payment_status/{order.order_id}/?payment_status=paid')
    
    else:
        return redirect(f'/payment_status/{order.order_id}/?payment_status=failed')
    

def payment_status(request, order_id):
    order = store_models.Order.objects.get(order_id=order_id)
    payment_status = request.GET.get('payment-status')

    context = {
        'order': order,
        'payment-status': payment_status,
    }
    
    return render(request, 'store/payment-status.html', context)


@csrf_exempt
def stripe_payment(request, order_id):
    order = store_models.Order.objects.get(order_id=order_id)

    checkout_session = stripe.checkout.Session.create(
        customer_email = order.address.email,
        payment_method_types = ['card'],
        line_items = [
            {
                'price_data': {
                    'currency': 'USD',
                    'product_data': {
                        'name': order.address.full_name
                    },
                    'unit_amount': int(order.total * 100)
                },
                'quantity': 1
            }
        ],
        mode = 'payment',
        success_url = request.build_absolute_uri(reverse('store:stripe-payment-verify', args=[order.order_id])) + '?session_id={CHECKOUT_SESSION_ID}' + '&payment_method=Stripe',
        cancel_url = request.build_absolute_uri(reverse('store:stripe-payment-verify', args=[order.order_id])),
    )

    print('Checkout Session: ', checkout_session)
    return JsonResponse({'sessionId': checkout_session.id})


def stripe_payment_verify(request, order_id):
    order = store_models.Order.objects.get(order_id=order_id)

    session_id = request.GET.get('session_id')
    session = stripe.checkout.Session.retrieve(session_id)

    if session.payment_status == 'paid':
        if order.payment_status == 'Processing':
            order.payment_status = 'Paid'
            order.payment_method = 'Stripe'
            order.save()
            clear_cart_items(request)


            # Send Email to Customer
            customer_merge_data = {
                'order': order,
                'order_items': order.order_items()
            }

            subject = f'New Order'
            text_body = render_to_string('email/order/customer/customer-new-order.txt', customer_merge_data)
            html_body = render_to_string('email/order/customer/customer-new-order.html', customer_merge_data)

            msg = EmailMultiAlternatives(
                subject=subject, from_email=settings.FROM_EMAIL,
                to=[order.address.email], body=text_body
            )

            msg.attach_alternative(html_body, 'text/html')
            msg.send()
            customer_models.Notification.objects.create(type='New Order', user=request.user)


            # Send Email to Vendor
            for item in order.order_items():
                vendor_merge_data = {
                    'item': item
                }

            subject = f'New Sale'
            text_body = render_to_string('email/order/vendor/vendor-new-order.txt', vendor_merge_data)
            html_body = render_to_string('email/order/vendor/vendor-new-order.html', vendor_merge_data)

            msg = EmailMultiAlternatives(
                subject=subject, from_email=settings.FROM_EMAIL,
                to=[item.vendor.email], body=text_body
            )

            msg.attach_alternative(html_body, 'text/html')
            msg.send()
            vendor_models.Notification.objects.create(type='New Order', user=item.vendor, order=item)

            return redirect(f'/payment_status/{order.order_id}?/payment_status=paid')
        
    return redirect(f'/payment_status/{order.order_id}?/payment_status=failed')


def paystack_payment_verify(request, order_id):
    order = store_models.Order.objects.get(order_id=order_id)
    reference = request.GET.get('reference', '')

    if reference:
        headers = {
            'Authorization': f'Bearer {settings.PAYSTACK_PRIVATE_KEY}',
            'Content-Type': 'application/json'
        }

        response = requests.get(f'https://api.paystack.com/transaction/verify/{reference}', headers=headers)
        response_data = response.json()

        if response_data['status']:
            if response_data['data']['status'] == 'success':
                if order.payment_status == 'Processing':
                    order.payment_status = 'Paid'
                    order.save()
                    clear_cart_items(request)

                    # Send Email to Customer

                    # Send InApp Notification

                    # Send Email to Vendor

                    return redirect(f'/payment_status/{order.order_id}?/payment_status=paid')
        
        else:
            return redirect(f'/payment_status/{order.order_id}?/payment_status=failed')
        

def flutterwave_payment_verify(request, order_id):
    order = store_models.Order.objects.get(order_id=order_id)
    tx_ref = request.GET.get("reference", "")

    headers = {
            'Authorization': f'Bearer {settings.FLUTTERWAVE_PRIVATE_KEY}',
            'Content-Type': 'application/json'
        }
    
    response = requests.get(f'https://api.flutterwave.com/v3/transactions/verify_by_reference?tx_ref={tx_ref}', headers=headers)
    response_data = response.json()

    if response_data['data']['status'] == 'successful':
        if order.payment_status == 'Processing':
            order.payment_status = 'Paid'
            order.save()
            clear_cart_items(request)

            # Send Email to Customer

            # Send InApp Notification

            # Send Email to Vendor

            return redirect(f'/payment_status/{order.order_id}?/payment_status=paid')
        
    return redirect(f'/payment_status/{order.order_id}?/payment_status=failed')


def flutterwave_payment_callback(request, order_id):
    order = store_models.Order.objects.get(order_id=order_id)
    tx_ref = request.GET.get('tx_ref', '')

    headers = {
            'Authorization': f'Bearer {settings.FLUTTERWAVE_PRIVATE_KEY}',
            'Content-Type': 'application/json'
        }
    
    response = requests.get(f'https://api.flutterwave.com/v3/charges/verify_by_reference?tx_ref={tx_ref}', headers=headers)

    if response.status_code == 200:
        if order.payment_status == 'Processing':
            order.payment_status = 'Paid'
            order.payment_method = 'Flutterwave'
            order.save()
            clear_cart_items(request)

            # Send Email to Customer

            # Send InApp Notification

            # Send Email to Vendor

            return redirect(f'/payment_status/{order.order_id}?/payment_status=paid')
        
    return redirect(f'/payment_status/{order.order_id}?/payment_status=failed')


@csrf_exempt
def razorpay_payment_verify(request, order_id):
    order = store_models.Order.objects.get(order_id=order_id)
    payment_method = request.GET.get('payment_method')

    if request.method == 'POST':
        data = request.POST

        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_signature = data.get('razorpay_signature')

        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature,
        }


        try:
            razorpay_client.utility.verify_payment_signature(params_dict)
            if order.payment_status == 'Processing':
                order.payment_method = 'RazorPay'
                order.save()
                clear_cart_items(request)

                # Send Email to Customer

                # Send InApp Notification

                # Send Email to Vendor

                return redirect(f'/payment_status/{order.order_id}?/payment_status=paid')
        except razorpay.errors.SignatureVerificationError: 
            return redirect(f'/payment_status/{order.order_id}?/payment_status=failed')
        

