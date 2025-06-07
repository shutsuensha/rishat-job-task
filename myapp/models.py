from decimal import ROUND_HALF_UP, Decimal

from django.db import models

CURRENCY_CHOICES = [
    ("USD", "US Dollar"),
    ("RUB", "Russian Ruble"),
]


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Item(TimestampedModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Item"
        verbose_name_plural = "Items"

    def __str__(self):
        return f"Item - {self.id} - {self.name} - {self.currency}"


class Discount(models.Model):
    name = models.CharField(max_length=255)
    percent = models.DecimalField(
        max_digits=5, decimal_places=2, help_text="Скидка в процентах на весь заказ"
    )

    def __str__(self):
        return f"{self.name} (-{self.percent}%) на весь заказ"


class Tax(models.Model):
    name = models.CharField(max_length=255)
    percent = models.DecimalField(
        max_digits=5, decimal_places=2, help_text="Налог в процентах на каждый товар в заказе"
    )

    def __str__(self):
        return f"{self.name} (+{self.percent}%) на каждый товар в заказе"


class Order(TimestampedModel):
    items = models.ManyToManyField(Item)
    discount = models.ForeignKey(Discount, on_delete=models.SET_NULL, null=True, blank=True)
    tax = models.ForeignKey(Tax, on_delete=models.SET_NULL, null=True, blank=True)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Order"
        verbose_name_plural = "Orders"

    def total_price(self):
        items_total = sum(Decimal(item.price) for item in self.items.all())

        discount_percent = Decimal(self.discount.percent) if self.discount else Decimal("0")
        discount_amount = items_total * discount_percent / Decimal("100")
        subtotal_after_discount = items_total - discount_amount

        tax_percent = Decimal(self.tax.percent) if self.tax else Decimal("0")
        tax_amount = subtotal_after_discount * tax_percent / Decimal("100")

        total = subtotal_after_discount + tax_amount
        return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def __str__(self):
        return f"Order - {self.id} - {self.currency}"
