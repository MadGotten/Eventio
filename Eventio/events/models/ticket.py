from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models, IntegrityError, transaction
from django.db.models import F
from events.models import Purchase


class Ticket(models.Model):
    event = models.OneToOneField("Event", on_delete=models.CASCADE, related_name="ticket")
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(1), MaxValueValidator(1000)],
    )
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100000)]
    )

    @property
    def price_to_cents(self):
        return int(self.price * 100)

    @staticmethod
    @transaction.atomic
    def buy(user, event, quantity, amount_paid=0):
        ticket = Ticket.objects.select_for_update().get(event=event)

        if ticket.quantity <= 0 or ticket.quantity < quantity:
            raise IntegrityError("Ticket quantity insufficient")

        ticket.quantity = F("quantity") - quantity
        ticket.save()

        purchase = Purchase.objects.create(
            ticket=ticket,
            user=user,
            quantity=quantity,
            event_name=event.title,
            amount_paid=amount_paid,
        )
        return purchase

    def __str__(self):
        return f"Ticket for {self.event.title} price {self.price}"
