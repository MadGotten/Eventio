from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models.events import Event


@receiver(post_delete, sender=Event)
def delete_cascade_event_img(sender, instance, **kwargs):
    """Cleanup associated image in bucket after event deletion"""
    if instance.banner:
        instance.banner.delete(save=False)
