from io import BytesIO
import logging
import uuid
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models, IntegrityError, transaction
from django.contrib.auth.models import User
from django.db.models import F
from PIL import Image, ImageOps
from django.core.files.base import ContentFile
from django.urls import reverse
from django.db.models.signals import post_delete
from django.dispatch import receiver

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


class Event(models.Model):
    EVENT_TYPE_CHOICES = [
        ("free", "Free"),
        ("paid", "Paid"),
    ]
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=200)
    date = models.DateTimeField()
    category = models.CharField(max_length=100)
    banner = models.ImageField(upload_to="banners/", null=True, blank=True)
    event_type = models.CharField(max_length=4, choices=EVENT_TYPE_CHOICES, default="free")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="events")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    @property
    def is_free(self):
        return self.event_type == "free"

    @property
    def is_paid(self):
        return self.event_type == "paid"

    def is_allowed_to_view(self, user):
        return user.is_staff or self.created_by == user

    def get_absolute_url(self):
        return reverse("event_detail", kwargs={"pk": self.pk})

    def save(self, *args, **kwargs):
        if self.banner:
            old_banner = None
            try:
                old_banner = Event.objects.get(pk=self.pk).banner
                if old_banner and old_banner.url == self.banner.url:
                    return super().save(*args, **kwargs)
            except Event.DoesNotExist:
                pass

            try:
                img = Image.open(self.banner)
                img.verify()
                img = Image.open(self.banner)

                if img.mode in ("RGBA", "LA", "P"):
                    img = img.convert("RGB")

                img = ImageOps.contain(img, (500, 300))
                temp_img = BytesIO()
                img.save(temp_img, format="WEBP", optimize=True, quality=95)
                temp_img.seek(0)

                new_filename = f"{uuid.uuid4()}.webp"

                self.banner.save(new_filename, ContentFile(temp_img.read()), save=False)

                if old_banner:
                    old_banner.delete(save=False)

            except (IOError, SyntaxError) as e:
                raise ValueError(f"The uploaded file is not a valid image: {e}")

        super().save(*args, **kwargs)


@receiver(post_delete, sender=Event)
def delete_cascade_event_img(sender, instance, **kwargs):
    """Cleanup associated image in bucket after event deletion"""
    if instance.banner:
        instance.banner.delete(save=False)


class Registration(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="registartions")
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="registrations")
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["user", "event"]

    def __str__(self):
        return f"{self.user.username} registered for {self.event.title}"


class Ticket(models.Model):
    event = models.OneToOneField(Event, on_delete=models.CASCADE, related_name="ticket")
    price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(1), MaxValueValidator(1000)]
    )
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100000)]
    )

    @staticmethod
    @transaction.atomic
    def buy(user, event, quantity):
        ticket = Ticket.objects.select_for_update().get(event=event)

        if ticket.quantity <= 0 or ticket.quantity < quantity:
            raise IntegrityError("Ticket quantity insufficient")

        ticket.quantity = F("quantity") - quantity
        ticket.save()

        purchase = Purchase.objects.create(ticket=ticket, user=user, quantity=quantity)
        return purchase

    def __str__(self):
        return f"Ticket for {self.event.title} price {self.price}"


class Purchase(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="purchases")
    quantity = models.PositiveIntegerField(default=1)
    purchased_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} bought ticket for {self.ticket.event.title}"

    @property
    def total(self):
        return self.quantity * self.ticket.price


class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["user", "event"]
        ordering = ["-created_at"]

    def __str__(self):
        return f"Review by {self.user.username} for {self.event.title} - {self.rating}"
