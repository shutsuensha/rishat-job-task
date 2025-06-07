import stripe
from django.conf import settings
from django.shortcuts import get_object_or_404, render

from .models import Item, Order


def item_detail_intent(request, id):
    item = get_object_or_404(Item, pk=id)
    currency = item.currency

    stripe.api_key = settings.STRIPE_KEYS[currency]["secret"]

    intent = stripe.PaymentIntent.create(
        amount=int(item.price * 100),
        currency=currency.lower(),
        metadata={"item_id": str(item.id)},
    )

    return render(
        request,
        "intent/items/item_detail_intent.html",
        {
            "item": item,
            "stripe_public_key": settings.STRIPE_KEYS[currency]["public"],
            "client_secret": intent.client_secret,
        },
    )


def payment_success_item_intent(request, id):
    item = get_object_or_404(Item, pk=id)
    return render(request, "intent/items/payment_success_item_intent.html", {"item": item})


def order_detail_intent(request, id):
    order = get_object_or_404(
        Order.objects.select_related("tax", "discount").prefetch_related("items"), pk=id
    )

    currency = order.currency

    items_total = sum(item.price for item in order.items.all())

    discount_percent = order.discount.percent if order.discount else 0
    discount_amount = items_total * discount_percent / 100

    subtotal_after_discount = items_total - discount_amount

    tax_percent = order.tax.percent if order.tax else 0
    tax_amount = subtotal_after_discount * tax_percent / 100

    total_amount = subtotal_after_discount + tax_amount

    amount = int(total_amount * 100)

    stripe.api_key = settings.STRIPE_KEYS[currency]["secret"]

    intent = stripe.PaymentIntent.create(
        amount=amount,
        currency=currency.lower(),
        metadata={"order_id": str(order.id)},
    )

    return render(
        request,
        "intent/orders/order_detail_intent.html",
        {
            "order": order,
            "stripe_public_key": settings.STRIPE_KEYS[currency]["public"],
            "client_secret": intent.client_secret,
            "items_total": items_total,
            "discount_percent": discount_percent,
            "discount_amount": discount_amount,
            "tax_percent": tax_percent,
            "tax_amount": tax_amount,
            "total_amount": total_amount,
            "currency": currency,
        },
    )


def payment_success_order_intent(request, id):
    order = get_object_or_404(Order, pk=id)
    return render(request, "intent/orders/payment_success_order_intent.html", {"order": order})
