from django.apps import AppConfig


class GamificationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gamification'
    verbose_name = 'Gamification'

    def ready(self):
        # Wire signals.
        from . import signals  # noqa: F401
