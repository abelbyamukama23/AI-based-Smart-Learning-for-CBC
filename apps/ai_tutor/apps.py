"""ai_tutor app configuration."""
from django.apps import AppConfig


class AiTutorConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.ai_tutor"
    label = "ai_tutor"
    verbose_name = "AI Tutor"
