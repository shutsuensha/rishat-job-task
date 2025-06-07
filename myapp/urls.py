from django.urls import path

from . import views, views_intent

urlpatterns = [
    path("", views.index, name="index"),
    path("item/<int:id>/", views.item_detail, name="item_detail"),
    path("buy/<int:id>/", views.buy_item, name="buy_item"),
    path("success/item/<int:id>/", views.payment_success_item, name="payment_success_item"),
    path("order/<int:id>/", views.order_detail, name="order_detail"),
    path("buy/order/<int:id>/", views.buy_order, name="buy_order"),
    path("success/order/<int:id>/", views.payment_success_order, name="payment_success_order"),
    path("intent/item/<int:id>/", views_intent.item_detail_intent, name="item_detail_intent"),
    path(
        "intent/success/item/<int:id>/",
        views_intent.payment_success_item_intent,
        name="payment_success_item_intent",
    ),
    path("intent/order/<int:id>/", views_intent.order_detail_intent, name="order_detail_intent"),
    path(
        "intent/success/order/<int:id>/",
        views_intent.payment_success_order_intent,
        name="payment_success_order_intent",
    ),
]
