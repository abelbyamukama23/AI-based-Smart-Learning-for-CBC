"""feed app configuration."""
from django.apps import AppConfig


class FeedConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.feed"
    label = "feed"
    verbose_name = "Knowledge Feed"
