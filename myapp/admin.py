from django.contrib import admin

from .forms import OrderForm
from .models import Discount, Item, Order, Tax


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "description", "price", "currency")
    list_filter = ("currency",)
    search_fields = ("name", "description")
    ordering = ("-created_at",)


@admin.register(Tax)
class TaxAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "percent")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "percent")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    form = OrderForm

    list_display = ("id", "currency", "total_price_display", "discount_display", "tax_display")
    list_filter = ("currency",)
    ordering = ("-created_at",)
    filter_horizontal = ("items",)

    def total_price_display(self, obj):
        return f"{obj.total_price()} {obj.currency}"

    total_price_display.short_description = "Total Price"

    def discount_display(self, obj):
        if obj.discount:
            return f"{obj.discount.name} ({obj.discount.percent}%)"
        return "-"

    discount_display.short_description = "Discount"

    def tax_display(self, obj):
        if obj.tax:
            return f"{obj.tax.name} ({obj.tax.percent}%)"
        return "-"

    tax_display.short_description = "Tax"
