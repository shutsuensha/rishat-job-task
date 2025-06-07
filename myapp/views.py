import stripe
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

from .models import Item, Order


def index(request):
    return render(request, "index.html")


def item_detail(request, id):
    item = get_object_or_404(Item, pk=id)
    currency = item.currency

    return render(
        request,
        "items/item_detail.html",
        {"item": item, "stripe_public_key": settings.STRIPE_KEYS[currency]["public"]},
    )


def buy_item(request, id):
    item = get_object_or_404(Item, pk=id)
    currency = item.currency

    if currency not in settings.STRIPE_KEYS:
        return JsonResponse({"error": f"Unsupported currency: {currency}"}, status=400)

    stripe.api_key = settings.STRIPE_KEYS[currency]["secret"]

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": currency.lower(),
                        "product_data": {
                            "name": item.name,
                        },
                        "unit_amount": int(item.price * 100),
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url=request.build_absolute_uri(f"/success/item/{item.id}/"),
            cancel_url=request.build_absolute_uri(f"/item/{item.id}/"),
        )
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"sessionId": session.id})


def payment_success_item(request, id):
    item = get_object_or_404(Item, pk=id)
    return render(request, "items/payment_success_item.html", {"item": item})


def order_detail(request, id):
    order = get_object_or_404(
        Order.objects.select_related("tax", "discount").prefetch_related("items"), pk=id
    )

    currency = order.currency

    return render(
        request,
        "orders/order_detail.html",
        {
            "order": order,
            "stripe_public_key": settings.STRIPE_KEYS[currency]["public"],
        },
    )


def buy_order(request, id):
    order = get_object_or_404(
        Order.objects.select_related("discount", "tax").prefetch_related("items"), pk=id
    )
    currency = order.currency

    if currency not in settings.STRIPE_KEYS:
        return JsonResponse({"error": f"Unsupported currency: {currency}"}, status=400)

    stripe.api_key = settings.STRIPE_KEYS[currency]["secret"]

    line_items = []
    for item in order.items.all():
        line_items.append(
            {
                "price_data": {
                    "currency": currency.lower(),
                    "product_data": {"name": item.name},
                    "unit_amount": int(item.price * 100),
                },
                "quantity": 1,
            }
        )

    discounts = []
    if order.discount and order.discount.percent > 0:
        coupon = stripe.Coupon.create(
            percent_off=float(order.discount.percent), duration="once", name=order.discount.name
        )
        discounts.append({"coupon": coupon.id})

    tax_rate_id = None
    if order.tax and order.tax.percent > 0:
        currency_country_map = {
            "USD": "US",
            "RUB": "RU",
        }
        country = currency_country_map[order.currency]

        tax_rate = stripe.TaxRate.create(
            display_name=order.tax.name,
            inclusive=False,
            percentage=float(order.tax.percent),
            country=country,
        )
        tax_rate_id = tax_rate.id

    if tax_rate_id:
        for item in line_items:
            item["tax_rates"] = [tax_rate_id]

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=line_items,
            discounts=discounts,
            mode="payment",
            success_url=request.build_absolute_uri(f"/success/order/{order.id}/"),
            cancel_url=request.build_absolute_uri(f"/order/{order.id}"),
        )
        return JsonResponse({"sessionId": session.id})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


def payment_success_order(request, id):
    order = get_object_or_404(Order, pk=id)
    return render(request, "intent/orders/payment_success_order_intent.html", {"order": order})
