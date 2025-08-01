from django.apps import AppConfig


class EventConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "events"

    def ready(self):
        import events.signals  # noqa
