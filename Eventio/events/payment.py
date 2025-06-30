import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_API_SECRET


def start_checkout_session(
    success_url: str,
    cancel_url: str,
    price: int,
    product_data: dict[str, str],
    quantity: int = 1,
    currency: str = "usd",
) -> str:
    if "?session_id=" not in success_url:
        success_url += "?session_id={CHECKOUT_SESSION_ID}"

    checkout = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="payment",
        line_items=[
            {
                "price_data": {
                    "currency": currency,
                    "product_data": product_data,
                    "unit_amount": price,
                },
                "quantity": quantity,
            }
        ],
        metadata={
            "product_id": product_data["name"],
            "quantity": quantity,
        },
        success_url=success_url,
        cancel_url=cancel_url,
    )

    if checkout.url is None:
        raise stripe.error.StripeError("Failed to create checkout session")

    return checkout.url


def get_checkout_session(session_id: str) -> stripe.checkout.Session:
    return stripe.checkout.Session.retrieve(session_id)
