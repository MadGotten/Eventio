from django.db import models
from django.contrib.auth.models import User


class Registration(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="registartions")
    event = models.ForeignKey("Event", on_delete=models.CASCADE, related_name="registrations")
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["user", "event"]

    def __str__(self):
        return f"{self.user.username} registered for {self.event.title}"
