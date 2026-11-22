import json
from .models import *

def _ensure_session(request):
	if not request.session.session_key:
		request.session.save()
	return request.session.session_key

def get_or_create_session_order(request, create=False):
    session_key = _ensure_session(request)
    order = Order.objects.filter(
        session_key=session_key,
        customer__isnull=True,
        complete=False
    ).first()
    if not order and create:
        order = Order.objects.create(session_key=session_key, complete=False)
    return order

def cartData(request):
    if request.user.is_authenticated:
        customer = request.user.customer
        order = Order.objects.filter(customer=customer, complete=False).first()
    else:
        order = get_or_create_session_order(request)

    if order:
        # Load both product and variant (and variant's product) to avoid N+1
        items = order.orderitem_set.select_related('product', 'variant__product').all()

        # Ensure every orderItem has a product even if only variant exists
        for item in items:
            if not item.product and item.variant:
                item.product = item.variant.product
                item.save()
         # 🛒 DEBUG PRINT
        print("🛒 Cart items now:")
        for i in items:
            print(" -", i.product.name, "| variant:", i.variant, "| price used:", i.unit_price)

        cartItems = order.get_cart_items
    else:
        items = []
        cartItems = 0

    return {'cartItems': cartItems, 'order': order, 'items': items}



def merge_session_cart_to_user(request, user):

    if not hasattr(user, 'customer'):
        return  # only merge for normal site users

    session_key = request.session.session_key
    if not session_key:
        return

    guest_order = Order.objects.filter(session_key=session_key, customer__isnull=True, complete=False).first()
    if not guest_order:
        return

    user_order = Order.objects.filter(customer=user.customer, complete=False).first()
    if user_order:
        # Merge guest items into existing user order
        for g_item in guest_order.orderitem_set.all():
            u_item, created = user_order.orderitem_set.get_or_create(
                product=g_item.product,
                variant=g_item.variant,
                defaults={'quantity': 0}
            )
            if created:
                u_item.quantity = g_item.quantity
            else:
                u_item.quantity += g_item.quantity
            u_item.save()
        guest_order.delete()
    else:
        # If no existing order, simply assign guest order to this user
        guest_order.customer = user.customer
        guest_order.session_key = None
        guest_order.save()
