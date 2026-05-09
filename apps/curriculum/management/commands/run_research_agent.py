"""
Management command: run_research_agent

Runs the Research Agent pipeline for a given topic or a list of default CBC topics.
Usage:
    python manage.py run_research_agent --topic "Photosynthesis" --subject "Biology" --level "S1"
    python manage.py run_research_agent --auto   # runs for all subjects/topics in DB
"""
import json
from django.core.management.base import BaseCommand


DEFAULT_TOPICS = [
    ("Photosynthesis",         "Biology",      "S1"),
    ("Linear Equations",       "Mathematics",  "S1"),
    ("Uganda Geography",       "SST",          "S1"),
    ("Parts of Speech",        "English",      "P6"),
    ("The Water Cycle",        "Science",      "P5"),
    ("HIV AIDS Prevention",    "Health",       "S2"),
    ("Food and Nutrition",     "Home Economics", "S1"),
    ("ICT and Society",        "ICT",          "S1"),
]


class Command(BaseCommand):
    help = "Run the Research Agent to discover and index new CBC curriculum content from the web."

    def add_arguments(self, parser):
        parser.add_argument("--topic",   type=str, default="", help="Specific topic to research")
        parser.add_argument("--subject", type=str, default="", help="Subject filter (e.g. Biology)")
        parser.add_argument("--level",   type=str, default="", help="Class level filter (e.g. S1)")
        parser.add_argument("--auto",    action="store_true",   help="Run for all default CBC topics")
        parser.add_argument("--max",     type=int, default=3,   help="Max sources per topic (default 3)")

    def handle(self, *args, **options):
        from apps.curriculum.research_agent import research_and_save

        self.stdout.write(self.style.MIGRATE_HEADING("\n[Research Agent] Starting curriculum discovery...\n"))

        if options["auto"]:
            topics = DEFAULT_TOPICS
        elif options["topic"]:
            topics = [(options["topic"], options["subject"], options["level"])]
        else:
            self.stdout.write(self.style.WARNING(
                "  Provide --topic <name> or --auto to run for default topics.\n"
                "  Example: python manage.py run_research_agent --topic 'Photosynthesis' --subject Biology --level S1\n"
            ))
            return

        total_approved = 0
        total_pending  = 0

        for topic, subject, level in topics:
            self.stdout.write(f"\n  [->] Researching: {topic} | {subject} | {level}")
            result = research_and_save(
                topic=topic,
                subject=subject,
                class_level=level,
                max_sources=options["max"],
            )

            for item in result["auto_approved"]:
                self.stdout.write(self.style.SUCCESS(
                    f"      [AUTO] {item['title'][:60]} (score={item['score']:.2f})"
                ))
                total_approved += 1

            for item in result["pending_review"]:
                self.stdout.write(self.style.WARNING(
                    f"      [PENDING] {item['title'][:60]} (score={item['score']:.2f}) -> review at /admin/"
                ))
                total_pending += 1

            if result["discarded"]:
                self.stdout.write(f"      [skip] {result['discarded']} sources discarded (low relevance)")

        self.stdout.write(self.style.SUCCESS(
            f"\n[DONE] Research complete: {total_approved} auto-approved, "
            f"{total_pending} pending admin review.\n"
        ))
