from django import forms
from django.core.exceptions import ValidationError

from .models import Order


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        currency = cleaned_data.get("currency")
        items = cleaned_data.get("items")

        if currency and items:
            for item in items:
                if item.currency != currency:
                    raise ValidationError(
                        f"Валюта товара '{item.name}' ({item.currency}) не совпадает с валютой заказа ({currency})."
                    )

        return cleaned_data
