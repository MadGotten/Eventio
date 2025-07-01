from django.db.models.signals import post_delete, post_save
from django.core.cache.utils import make_template_fragment_key
from django.dispatch import receiver
from django.core.cache import cache
from .models.events import Event


@receiver(post_delete, sender=Event)
def delete_cascade_event_img(sender, instance, **kwargs):
    """Cleanup associated image in bucket after event deletion"""
    if instance.banner:
        instance.banner.delete(save=False)


@receiver([post_delete, post_save], sender=Event)
def invalidate_event_cache(sender, instance, **kwargs):
    """Invalidate event cache after event deletion or creation"""
    key = make_template_fragment_key("event_list")
    cache.delete(key)
