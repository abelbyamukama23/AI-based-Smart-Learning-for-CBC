"""curriculum app configuration."""
import threading
from django.apps import AppConfig


class CurriculumConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.curriculum"
    label = "curriculum"
    verbose_name = "CBC Curriculum Content"

    def ready(self):
        """
        Called once when Django finishes loading.
        Triggers background pre-loading of the RAG embedding model + ChromaDB
        so the first learner query is fast (no cold-start penalty).
        """
        # Guard: only warm up in the main process, not in migrate/test commands
        import sys
        is_manage_command = (
            "migrate" in sys.argv
            or "makemigrations" in sys.argv
            or "test" in sys.argv
            or "collectstatic" in sys.argv
            or "createsuperuser" in sys.argv
        )
        if is_manage_command:
            return

        # Import signals to register them
        import apps.curriculum.signals

        # Defer import to avoid circular imports at startup
        def _start_warmup():
            try:
                from apps.curriculum.rag_service import warm_up_rag
                from apps.curriculum.auto_sync import start_auto_sync
                
                warm_up_rag()
                start_auto_sync()
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning("Startup hook failed: %s", e)

        # Small delay to let Django finish booting before we start the background threads
        t = threading.Timer(3.0, _start_warmup)
        t.daemon = True
        t.start()
