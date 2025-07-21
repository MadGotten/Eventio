from django.db import models
from django.contrib.auth.models import User


class Purchase(models.Model):
    ticket = models.ForeignKey("Ticket", on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="purchases")
    quantity = models.PositiveIntegerField(default=1)
    event_name = models.CharField(max_length=200)
    amount_paid = models.PositiveIntegerField()
    purchased_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} bought ticket for {self.event_name}"

    @property
    def total(self):
        return f"{self.amount_paid // 100}.{self.amount_paid % 100:02}"
