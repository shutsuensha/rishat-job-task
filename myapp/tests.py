# Create your tests here.
import json
from unittest.mock import MagicMock, patch

from django.conf import settings
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse

from .models import Discount, Item, Order, Tax
from .views import buy_item


class ItemDetailViewTest(TestCase):
    def setUp(self):
        self.item = Item.objects.create(name="Test Item", price=10.00, currency="USD")
        self.client = Client()

    def test_item_detail_view_status_code_and_context(self):
        url = reverse("item_detail", args=[self.item.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        self.assertIn("item", response.context)
        self.assertEqual(response.context["item"], self.item)

        self.assertIn("stripe_public_key", response.context)
        self.assertEqual(
            response.context["stripe_public_key"],
            settings.STRIPE_KEYS[self.item.currency]["public"],
        )

        self.assertTemplateUsed(response, "items/item_detail.html")


class BuyItemViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.item = Item.objects.create(
            name="Test Item",
            price=10.0,
            currency="USD",
        )

    @patch("stripe.checkout.Session.create")
    def test_buy_item_success(self, mock_stripe_create):
        mock_session = MagicMock()
        mock_session.id = "sess_12345"
        mock_stripe_create.return_value = mock_session

        request = self.factory.get(f"/buy/item/{self.item.id}/")
        response = buy_item(request, self.item.id)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn("sessionId", data)
        self.assertEqual(data["sessionId"], "sess_12345")

    def test_buy_item_unsupported_currency(self):
        self.item.currency = "EUR"
        self.item.save()
        request = self.factory.get(f"/buy/item/{self.item.id}/")
        response = buy_item(request, self.item.id)

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn("error", data)
        self.assertIn("Unsupported currency", data["error"])

    @patch("stripe.checkout.Session.create")
    def test_buy_item_stripe_exception(self, mock_stripe_create):
        mock_stripe_create.side_effect = Exception("Stripe error")

        request = self.factory.get(f"/buy/item/{self.item.id}/")
        response = buy_item(request, self.item.id)

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn("error", data)
        self.assertEqual(data["error"], "Stripe error")


class PaymentSuccessItemViewTest(TestCase):
    def setUp(self):
        self.item = Item.objects.create(
            name="Test Item",
            price=10.0,
            currency="USD",
        )

    def test_payment_success_item_view_returns_200(self):
        url = reverse("payment_success_item", args=[self.item.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("item", response.context)
        self.assertEqual(response.context["item"], self.item)

    def test_payment_success_item_view_404(self):
        url = reverse("payment_success_item", args=[9999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class OrderDetailViewTest(TestCase):
    def setUp(self):
        self.tax = Tax.objects.create(name="VAT", percent=10)
        self.discount = Discount.objects.create(name="Black Friday", percent=5)
        self.order = Order.objects.create(currency="USD", tax=self.tax, discount=self.discount)

        self.item1 = Item.objects.create(name="Item 1", price=100, currency="USD")
        self.item2 = Item.objects.create(name="Item 2", price=50, currency="USD")
        self.order.items.add(self.item1, self.item2)

    def test_order_detail_view_returns_200_and_correct_context(self):
        url = reverse("order_detail", args=[self.order.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("order", response.context)
        self.assertEqual(response.context["order"], self.order)
        self.assertIn("stripe_public_key", response.context)
        self.assertEqual(
            response.context["stripe_public_key"],
            settings.STRIPE_KEYS[self.order.currency]["public"],
        )

    def test_order_detail_view_404_for_nonexistent_order(self):
        url = reverse("order_detail", args=[9999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class BuyOrderViewTest(TestCase):
    def setUp(self):
        self.tax = Tax.objects.create(name="VAT", percent=10)
        self.discount = Discount.objects.create(name="Black Friday", percent=5)
        self.order = Order.objects.create(currency="USD", tax=self.tax, discount=self.discount)
        self.item1 = Item.objects.create(name="Item 1", price=100, currency="USD")
        self.order.items.add(self.item1)

    @patch("stripe.checkout.Session.create")
    @patch("stripe.Coupon.create")
    @patch("stripe.TaxRate.create")
    def test_buy_order_success(self, mock_taxrate_create, mock_coupon_create, mock_session_create):
        mock_session = MagicMock()
        mock_session.id = "sess_123"
        mock_session_create.return_value = mock_session

        mock_coupon = MagicMock()
        mock_coupon.id = "coupon_123"
        mock_coupon_create.return_value = mock_coupon

        mock_taxrate = MagicMock()
        mock_taxrate.id = "tax_123"
        mock_taxrate_create.return_value = mock_taxrate

        url = reverse("buy_order", args=[self.order.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIn("sessionId", response.json())
        self.assertEqual(response.json()["sessionId"], "sess_123")

        mock_session_create.assert_called_once()
        mock_coupon_create.assert_called_once()
        mock_taxrate_create.assert_called_once()

    def test_buy_order_unsupported_currency(self):
        self.order.currency = "XYZ"
        self.order.save()

        url = reverse("buy_order", args=[self.order.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())
        self.assertIn("Unsupported currency", response.json()["error"])

    @patch("stripe.checkout.Session.create")
    def test_buy_order_stripe_exception(self, mock_session_create):
        mock_session_create.side_effect = Exception("Stripe error")

        url = reverse("buy_order", args=[self.order.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())
        self.assertEqual(response.json()["error"], "Stripe error")


class ItemDetailIntentViewTest(TestCase):
    def setUp(self):
        self.item = Item.objects.create(name="Test Item", price=10.50, currency="USD")

    @patch("stripe.PaymentIntent.create")
    def test_item_detail_intent_success(self, mock_payment_intent_create):
        mock_intent = MagicMock()
        mock_intent.client_secret = "test_client_secret"
        mock_payment_intent_create.return_value = mock_intent

        url = reverse("item_detail_intent", args=[self.item.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "intent/items/item_detail_intent.html")
        self.assertIn("item", response.context)
        self.assertEqual(response.context["item"], self.item)
        self.assertEqual(
            response.context["stripe_public_key"],
            settings.STRIPE_KEYS[self.item.currency]["public"],
        )
        self.assertEqual(response.context["client_secret"], "test_client_secret")

        mock_payment_intent_create.assert_called_once_with(
            amount=int(self.item.price * 100),
            currency=self.item.currency.lower(),
            metadata={"item_id": str(self.item.id)},
        )


class PaymentSuccessItemIntentViewTest(TestCase):
    def setUp(self):
        self.item = Item.objects.create(name="Test Item", price=10.50, currency="USD")

    def test_payment_success_item_intent_view(self):
        url = reverse("payment_success_item_intent", args=[self.item.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "intent/items/payment_success_item_intent.html")
        self.assertIn("item", response.context)
        self.assertEqual(response.context["item"], self.item)


class OrderDetailIntentViewTest(TestCase):
    def setUp(self):
        self.discount = Discount.objects.create(name="Test Discount", percent=10)
        self.tax = Tax.objects.create(name="Test Tax", percent=5)
        self.order = Order.objects.create(currency="USD", discount=self.discount, tax=self.tax)
        self.item1 = Item.objects.create(name="Item 1", price=100, currency="USD")
        self.item2 = Item.objects.create(name="Item 2", price=200, currency="USD")
        self.order.items.add(self.item1, self.item2)

    @patch("stripe.PaymentIntent.create")
    def test_order_detail_intent_view(self, mock_payment_intent_create):
        mock_payment_intent_create.return_value.client_secret = "test_secret"

        url = reverse("order_detail_intent", args=[self.order.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "intent/orders/order_detail_intent.html")

        context = response.context
        self.assertIn("order", context)
        self.assertIn("stripe_public_key", context)
        self.assertIn("client_secret", context)
        self.assertIn("items_total", context)
        self.assertIn("discount_percent", context)
        self.assertIn("discount_amount", context)
        self.assertIn("tax_percent", context)
        self.assertIn("tax_amount", context)
        self.assertIn("total_amount", context)
        self.assertIn("currency", context)

        expected_items_total = self.item1.price + self.item2.price
        self.assertEqual(context["items_total"], expected_items_total)

        expected_discount_percent = self.discount.percent
        self.assertEqual(context["discount_percent"], expected_discount_percent)

        expected_discount_amount = expected_items_total * expected_discount_percent / 100
        self.assertAlmostEqual(context["discount_amount"], expected_discount_amount)

        subtotal_after_discount = expected_items_total - expected_discount_amount

        expected_tax_percent = self.tax.percent
        self.assertEqual(context["tax_percent"], expected_tax_percent)

        expected_tax_amount = subtotal_after_discount * expected_tax_percent / 100
        self.assertAlmostEqual(context["tax_amount"], expected_tax_amount)

        expected_total_amount = subtotal_after_discount + expected_tax_amount
        self.assertAlmostEqual(context["total_amount"], expected_total_amount)

        self.assertEqual(context["currency"], self.order.currency)

        mock_payment_intent_create.assert_called_once_with(
            amount=int(expected_total_amount * 100),
            currency=self.order.currency.lower(),
            metadata={"order_id": str(self.order.id)},
        )


class PaymentSuccessOrderIntentViewTest(TestCase):
    def setUp(self):
        self.order = Order.objects.create(currency="USD")

    def test_payment_success_order_intent_view(self):
        url = reverse("payment_success_order_intent", args=[self.order.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "intent/orders/payment_success_order_intent.html")
        self.assertIn("order", response.context)
        self.assertEqual(response.context["order"], self.order)
