from .base import *  # noqa: F401, F403
from .base import INSTALLED_APPS
from .base import MIDDLEWARE
from .base import STORAGES

DEBUG = True

SECRET_KEY = "django-insecure-*s551npzs)2x&&4@nbf&i=s#669wq)gu_7vp+4e6bp54391-#u"

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]

INTERNAL_IPS = [
    "127.0.0.1",
]

INSTALLED_APPS += ["debug_toolbar", "whitenoise.runserver_nostatic"]

MIDDLEWARE += [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "EMAIL_AUTHENTICATION": True,
        "APP": {
            "client_id": "123",
            "secret": "super_secret",
            "key": "",
        },
    }
}

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "database",
    }
}

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

STORAGES["default"] = {"BACKEND": "django.core.files.storage.FileSystemStorage"}
