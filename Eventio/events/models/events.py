import logging
import uuid
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from events.helpers import validate_image

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


class EventQueryset(models.QuerySet):
    def active(self):
        return self.filter(status="approved")

    def free(self):
        return self.filter(event_type="free")

    def paid(self):
        return self.filter(event_type="paid")

    def popular(self):
        return self.annotate(num_registers=models.Count("registrations")).order_by("-num_registers")

    def recent(self):
        return self.order_by("-created_at")


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

    objects = EventQueryset.as_manager()

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

    @property
    def is_active(self):
        return self.status == "approved"

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
                content_file = validate_image(self.banner)
                new_filename = f"{uuid.uuid4()}.webp"

                self.banner.save(new_filename, content_file, save=False)

                if old_banner:
                    old_banner.delete(save=False)

            except (IOError, SyntaxError) as e:
                raise ValueError(f"The uploaded file is not a valid image: {e}")

        super().save(*args, **kwargs)
