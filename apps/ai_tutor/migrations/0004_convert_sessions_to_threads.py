"""
Data migration: Convert existing isolated AISession rows (where thread is null)
into ChatThread containers.

Each old AISession becomes its own 1-interaction thread, titled after the
first 80 characters of its query, preserving all history in the new structure.
"""
from django.db import migrations
import uuid


def convert_sessions_to_threads(apps, schema_editor):
    ChatThread = apps.get_model("ai_tutor", "ChatThread")
    AISession = apps.get_model("ai_tutor", "AISession")

    orphaned = AISession.objects.filter(thread__isnull=True).order_by("timestamp")

    for session in orphaned:
        # Generate a readable title from the query
        title = session.query[:80] if session.query else "(Imported Session)"
        if len(session.query) > 80:
            title += "..."

        thread = ChatThread.objects.create(
            id=uuid.uuid4(),
            learner=session.learner,
            title=title,
            created_at=session.timestamp,
            updated_at=session.timestamp,
        )
        session.thread = thread
        session.save(update_fields=["thread"])

    count = orphaned.count() if hasattr(orphaned, 'count') else 0
    print(f"\n  Converted {AISession.objects.filter(thread__isnull=False).count()} sessions into threads.")


def reverse_migration(apps, schema_editor):
    # Simply un-link sessions from threads (threads will cascade-delete on reverse schema migration)
    AISession = apps.get_model("ai_tutor", "AISession")
    AISession.objects.update(thread=None)


class Migration(migrations.Migration):

    dependencies = [
        ("ai_tutor", "0003_add_chatthread_model"),
    ]

    operations = [
        migrations.RunPython(convert_sessions_to_threads, reverse_migration),
    ]
