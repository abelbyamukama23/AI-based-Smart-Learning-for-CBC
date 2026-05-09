"""
Management command: sync_from_r2

Scans the Cloudflare R2 bucket and creates CurriculumFile records for any
files that exist in R2 but have no matching database entry.

Usage:
    python manage.py sync_from_r2
    python manage.py sync_from_r2 --prefix library/     # only a subfolder
    python manage.py sync_from_r2 --dry-run             # preview without saving
"""
import os
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings


# Map file extensions to FileType choices
EXT_TYPE_MAP = {
    ".pdf":  "PDF",
    ".png":  "IMAGE",
    ".jpg":  "IMAGE",
    ".jpeg": "IMAGE",
    ".gif":  "IMAGE",
    ".webp": "IMAGE",
    ".mp3":  "AUDIO",
    ".wav":  "AUDIO",
    ".ogg":  "AUDIO",
    ".m4a":  "AUDIO",
    ".mp4":  "VIDEO",
    ".mov":  "VIDEO",
    ".webm": "VIDEO",
    ".svg":  "IMAGE",
}


def _ext_to_type(key: str) -> str:
    ext = Path(key).suffix.lower()
    return EXT_TYPE_MAP.get(ext, "OTHER")


def _key_to_title(key: str) -> str:
    """Convert an R2 object key to a human-readable title."""
    name = Path(key).stem              # filename without extension
    name = name.replace("-", " ").replace("_", " ")
    return name.title()


class Command(BaseCommand):
    help = (
        "Sync files from Cloudflare R2 into the Django CurriculumFile database. "
        "Creates DB records for files that are in R2 but not yet registered."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--prefix",
            type=str,
            default="",
            help="Only sync keys starting with this prefix (e.g. 'library/'). Default: all files.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="List what would be created without actually saving anything.",
        )

    def handle(self, *args, **options):
        import boto3
        from apps.curriculum.models import CurriculumFile

        dry_run = options["dry_run"]
        prefix  = options["prefix"]

        if not getattr(settings, "AWS_ACCESS_KEY_ID", ""):
            self.stdout.write(self.style.ERROR(
                "R2 credentials not configured in settings. "
                "Check CLOUDFLARE_R2_ACCESS_KEY_ID in your .env file."
            ))
            return

        mode = "[DRY RUN] " if dry_run else ""
        self.stdout.write(self.style.MIGRATE_HEADING(
            f"\n{mode}Syncing R2 bucket: {settings.AWS_STORAGE_BUCKET_NAME}\n"
        ))

        # ── 1. Connect to R2 ───────────────────────────────────────────────────
        s3 = boto3.client(
            "s3",
            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name="auto",
        )

        # ── 2. List all objects in the bucket ─────────────────────────────────
        self.stdout.write(f"  Listing objects{' (prefix: ' + prefix + ')' if prefix else ''}...")
        paginator = s3.get_paginator("list_objects_v2")
        pages = paginator.paginate(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            **({"Prefix": prefix} if prefix else {}),
        )

        all_keys = []
        for page in pages:
            for obj in page.get("Contents", []):
                all_keys.append(obj["Key"])

        if not all_keys:
            self.stdout.write(self.style.WARNING("  No objects found in bucket."))
            return

        self.stdout.write(f"  Found {len(all_keys)} object(s) in R2.\n")

        # ── 3. Get existing DB keys to avoid duplicates ────────────────────────
        existing_keys = set(CurriculumFile.objects.values_list("file", flat=True))

        # ── 4. Create missing records ──────────────────────────────────────────
        created = 0
        skipped = 0

        for key in all_keys:
            # Skip folder markers and hidden files
            if key.endswith("/") or Path(key).name.startswith("."):
                continue

            if key in existing_keys:
                self.stdout.write(f"  [skip]    {key[:70]}  (already in DB)")
                skipped += 1
                continue

            title     = _key_to_title(key)
            file_type = _ext_to_type(key)

            if dry_run:
                self.stdout.write(
                    self.style.WARNING(f"  [dry-run] Would create: [{file_type}] {title}  ({key})")
                )
                created += 1
                continue

            try:
                CurriculumFile.objects.create(
                    title     = title,
                    file      = key,           # Store the R2 key as the file path
                    file_type = file_type,
                    source    = f"R2 sync — {key}",
                    description = (
                        f"Imported from R2 bucket. "
                        f"Edit this record in /admin/ to add subject, level, and tags."
                    ),
                )
                self.stdout.write(self.style.SUCCESS(
                    f"  [created] [{file_type}] {title[:55]}  ({key})"
                ))
                created += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  [error]   {key}: {e}"))

        # ── 5. Summary ────────────────────────────────────────────────────────
        self.stdout.write(self.style.SUCCESS(
            f"\n{mode}Done: {created} record(s) {'would be ' if dry_run else ''}created, "
            f"{skipped} skipped (already in DB).\n"
        ))

        if created > 0 and not dry_run:
            self.stdout.write(
                "  Next steps:\n"
                "  1. Visit /admin/ -> Library Files to set subject, level, and tags.\n"
                "  2. Run:  python manage.py build_library_index\n"
                "     to embed the new files into ChromaDB for Mwalimu search.\n"
            )
