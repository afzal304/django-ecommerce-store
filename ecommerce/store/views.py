import json
from django.shortcuts import render
from django.http import JsonResponse
from .models import *
import datetime
from . utils import cartData
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import redirect, get_object_or_404
from django.http import HttpResponse
from decimal import Decimal
from django.contrib import messages
from .utils import cartData, get_or_create_session_order, merge_session_cart_to_user
from django.core.paginator import Paginator

# Create your views here.
def store(request):
    data = cartData(request)

    cartItems = data['cartItems']
    #order = data['order']
    #items = data['items']

    # get category filter from URL
    category_id = request.GET.get('category')

    if category_id:
        products = Product.objects.filter(category_id=category_id)
    else:
        products = Product.objects.all().prefetch_related("variants")
        for p in products:
            p.has_variants = p.variants.exists()

    context = {
        'products': products,
        'cartItems': cartItems,
    }
    return render(request, 'store/store.html', context)

def product_detail(request, pk):
    data = cartData(request)
    cartItems = data['cartItems']
    product = get_object_or_404(Product, pk=pk)

    # Get variants for this product
    variants_qs = Variant.objects.filter(product=product)

    # Prepare JSON-safe data
    variants = [
        {
            "id": v.id,
            "color": v.color,
            "size": v.size,
            "price": float(v.price),
            "stock": v.stock,
        }
        for v in variants_qs
    ]

    # Distinct colors & sizes for buttons
    colors = variants_qs.values_list("color", flat=True).distinct()
    sizes = variants_qs.values_list("size", flat=True).distinct()

    context = {
        "product": product,
        "cartItems" : cartItems,
        "main_image": product.image if product.image else None,
        "extra_images": product.images.all(),
        "variants": json.dumps(variants),  # ✅ send JSON string to template
        "has_variants": variants_qs.exists(),    # ✅ boolean for template
        "colors": colors,
        "sizes": sizes,
    }
    return render(request, "store/product_detail.html", context)

def cart(request):
    data = cartData(request)

    cartItems = data['cartItems']
    order = data['order']
    items = data['items']

    # ✅ Validate stock before rendering
    for item in items:
        product = item.product
        variant = getattr(item, 'variant', None)
        available_stock = variant.stock if variant else product.stock

        # Item exceeds available stock
        if item.quantity > available_stock:
            if available_stock > 0:
                item.quantity = available_stock
                item.save()
                messages.warning(
                    request,
                    f"⚠️ Only {available_stock} of '{product.name}' available. Quantity adjusted."
                )
            else:
                item.delete()
                messages.error(
                    request,
                    f"❌ '{product.name}' is sold out and removed from your cart."
                )

    # Refresh data after cleanup
    data = cartData(request)
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']

    context = {
        'items': items,
        'order': order,
        'cartItems': cartItems,
        'shipping': False,
    }
    return render(request, 'store/cart.html', context)

def checkout(request):
    data = cartData(request)

    cartItems = data['cartItems']
    order = data['order']
    items = data['items']

    is_fetch = request.headers.get('X-Custom-Request') == 'fetch-checkout'

    if cartItems == 0:
        if is_fetch:
            return JsonResponse({
                'status': 'error',
                'message': 'Add item for checkout'
            })
        messages.warning(request, "Your cart is empty, add products to checkout")
        return redirect('cart')

    if is_fetch:
        return JsonResponse({'status': 'success'})

    context = {'items': items, 'order': order, 'cartItems': cartItems, 'shipping': False}
    return render(request, 'store/checkout.html', context)

# store/views.py
def updateItem(request):
    data = json.loads(request.body)
    productId = data.get('productId')
    variantId = data.get('variantId')
    action = data['action']

    product = Product.objects.get(id=productId)

    if request.user.is_authenticated:
        customer = request.user.customer
        order = Order.objects.filter(customer=customer, complete=False).first()
        if not order and action == "add":
            order = Order.objects.create(customer=customer, complete=False)
    else:
        # Guest session order
        order = get_or_create_session_order(request, create=(action == "add"))
        
    if not order:
        # No order exists and user is trying to remove -> return safely
        return JsonResponse({'cart_Items':0},safe=False)
    if variantId:
        variant = Variant.objects.get(id=variantId)
        product = variant.product
        current_stock = variant.stock
    else:
        variant = None
        current_stock = product.stock
        
    if action == 'add' and current_stock <= 0:
        return JsonResponse({
            'error': 'out_of_stock',
            'message': f"'{product.name}' is out of stock.",
            'productId': productId,
            'variantId': variantId,
            }, safe=False)

    # ✅ Only create order item if stock > 0
    orderItem, created = OrderItem.objects.get_or_create(
        order=order,
        product=product,
        variant=variant,
        )
    # ===============================
    # 🚀 Add / Remove logic
    # ===============================
    if action == "add":
        if orderItem.quantity < current_stock:
            orderItem.quantity += 1
            orderItem.save()
        else:
            return JsonResponse({
                'error': 'insufficient_stock',
                #'message': f"Only {current_stock} left for '{product.name}'.",
                'message': f"insufficient_stock left for '{product.name}'.",
                'productId': productId,
                'variantId': variantId,
                }, safe=False)

    elif action == 'remove':
        orderItem.quantity -= 1
    if orderItem.quantity <= 0:
        orderItem.delete()
    else:
        orderItem.save()
    # --- Clean up if no items left ---
    if order.orderitem_set.count() == 0:
        order.delete()
        return JsonResponse({
            'productId':productId,
            'quantity':0,
            'item_total':0,
            'cart_total':0,
            'cart_items':0,
        }, safe=False)
    print("Order items now:", order.orderitem_set.all())  # 👈 Debug
    #return JsonResponse({'status': 'ok', 'items': order.get_cart_items}, safe=False)

    # --- Normal response ---
    response = {
        'productId': productId,
        'variantId' : variantId,
        'quantity': orderItem.quantity if orderItem.id else 0,
        'item_total': float(orderItem.get_total) if orderItem.id else 0,
        'cart_total': float(order.get_cart_total),
        'cart_items': order.get_cart_items,
    }
    return JsonResponse(response, safe=False)
# store/views.py
def processOrder(request):
    transaction_id = datetime.datetime.now().timestamp()
    data = json.loads(request.body)

    if request.user.is_authenticated:
        customer = request.user.customer
        order = Order.objects.filter(customer=customer, complete=False).first()
    else:
        order = get_or_create_session_order(request)
        customer = None

    if not order or order.get_cart_items == 0:
        return JsonResponse('No items in cart', safe=False)

    total = Decimal(data['form']['total'])
    order.transaction_id = transaction_id   # always set transaction id

    if total == order.get_cart_total:
        order.complete = True

        # ✅ Always create/link a customer for guest checkout
        if not request.user.is_authenticated:
            name = data['form'].get('name') or 'Guest'
            email = data['form'].get('email') or f"guest_{transaction_id}@example.com"

            customer, created = Customer.objects.get_or_create(
                email=email,
                defaults={'name': name}
            )
            if not customer.name and name:
                customer.name = name
                customer.save()

            order.customer = customer   # attach customer

        order.save()

        #Decrease Stock
        for item in order.orderitem_set.all():
            if item.variant:
                # If product has variants, reduce variant stock
                if item.variant.stock >= item.quantity:
                    item.variant.stock -= item.quantity
                    item.variant.save()
                else:
                    item.variant.stock = 0
                    item.variant.save()
            else:
                # Reduce base product stock
                if item.product.stock >= item.quantity:
                    item.product.stock -= item.quantity
                    item.product.save()
                else:
                    item.product.stock = 0
                    item.product.save()
        # Save shipping if needed
        if order.shipping:
            ShippingAddress.objects.create(
                customer=order.customer,
                order=order,
                address=data['shipping'].get('address', ''),
                city=data['shipping'].get('city', ''),
                state=data['shipping'].get('state', ''),
                zipcode=data['shipping'].get('zipcode', ''),
            )

    else:
        return JsonResponse('Total mismatch error', safe=False)

    return JsonResponse('Payment submitted..', safe=False)

def signup_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        email    = request.POST['email']
        password = request.POST['password']
        if User.objects.filter(username=username).exists():
            return render(request, 'store/signup.html', {'error': 'this username exist try other'})
        user = User.objects.create_user(username=username, email=email, password=password)
        Customer.objects.create(user=user, name=username, email=email)

        merge_session_cart_to_user(request, user)  # NEW

        login(request, user)

        return redirect('store')
    return render(request, 'store/signup.html')

@login_required
def user_profile(request):
    customer = request.user.customer
    # Get all completed orders
    orders = Order.objects.filter(customer=customer, complete=True).order_by('-date_ordered')
    #pagination
    paginator = Paginator(orders, 5)
    page_number = request.GET.get('page')
    orders_page = paginator.get_page(page_number)
    context ={
        'customer': customer,
        'orders': orders_page,
    }
    return render(request, 'store/user_profile.html', context)

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, customer=request.user.customer, complete=True)

    # Get all items for this order
    items = order.orderitem_set.all()
    items_data = []
    for item in items:
        items_data.append({
            "product": item.product.name,
            # Safely show variant info if present
            "variant": f"{item.variant.color if item.variant else ''} {item.variant.size if item.variant else ''}".strip(),
            "quantity": item.quantity,
            "price": float(item.unit_price),         # ✅ use unit_price (variant or product price)
            "total": float(item.get_total),
        })

    # Get shipping info
    shipping = ShippingAddress.objects.filter(order=order).first()
    shipping_data = None
    if shipping:
        shipping_data = {
            "address": shipping.address,
            "city": shipping.city,
            "state": shipping.state,
            "zipcode": shipping.zipcode,
        }

    return JsonResponse({
        "items": items_data,
        "shipping": shipping_data
    })

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            if hasattr(user, 'customer') and not user.is_staff:

                merge_session_cart_to_user(request, user)  # NEW
                
                login(request, user)

                return redirect('store')
            else:
                return render(request, 'store/login.html', {'error': 'not authorized as website user'})
        else:
            return render(request, 'store/login.html', {'error': 'invalid credential'})
    return render(request, 'store/login.html')

def logout_view(request):
	logout(request)
	return redirect('store')

