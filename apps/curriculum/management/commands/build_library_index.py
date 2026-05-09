"""
Management command: build_library_index

Embeds all CurriculumFile records and Lesson body text into ChromaDB for RAG retrieval.
Run after uploading new files:  python manage.py build_library_index
Use --rebuild flag to re-embed everything from scratch.
"""
import os
import sys
import logging
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Build or update the ChromaDB RAG index from curriculum files and lessons."

    def add_arguments(self, parser):
        parser.add_argument(
            "--rebuild",
            action="store_true",
            help="Delete and rebuild the entire index from scratch.",
        )
        parser.add_argument(
            "--only-unindexed",
            action="store_true",
            default=True,
            help="Only embed files that have not been indexed yet (default).",
        )

    def handle(self, *args, **options):
        import chromadb
        from sentence_transformers import SentenceTransformer
        from apps.curriculum.models import CurriculumFile, Lesson

        self.stdout.write(self.style.MIGRATE_HEADING("\n[*] Building Library RAG Index...\n"))

        # ── 1. Initialise ChromaDB ──────────────────────────────────────────────
        chroma_path = settings.CHROMADB_PATH
        Path(chroma_path).mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=chroma_path)

        if options["rebuild"]:
            self.stdout.write("  [!] Rebuild mode -- deleting existing collections...")
            for col in ["curriculum_lessons", "curriculum_files"]:
                try:
                    client.delete_collection(col)
                except Exception:
                    pass

        lessons_col = client.get_or_create_collection(
            name="curriculum_lessons",
            metadata={"hnsw:space": "cosine"},
        )
        files_col = client.get_or_create_collection(
            name="curriculum_files",
            metadata={"hnsw:space": "cosine"},
        )

        # ── 2. Load embedding model ─────────────────────────────────────────────
        self.stdout.write("  [AI] Loading embedding model (all-MiniLM-L6-v2)...")
        model = SentenceTransformer("all-MiniLM-L6-v2")
        self.stdout.write(self.style.SUCCESS("  [OK] Model loaded.\n"))

        # ── 3. Embed Lessons (body_html + title + description) ──────────────────
        lessons = Lesson.objects.select_related("subject", "class_level").all()
        lesson_count = 0
        for lesson in lessons:
            doc_id = f"lesson_{lesson.id}"
            if not options["rebuild"]:
                existing = lessons_col.get(ids=[doc_id])
                if existing["ids"]:
                    continue

            text = f"{lesson.title}\n{lesson.description}\n{lesson.body_html}"
            text = text[:4000]

            embedding = model.encode(text).tolist()
            lessons_col.upsert(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[text],
                metadatas=[{
                    "title":       lesson.title,
                    "subject":     lesson.subject.subject_name if lesson.subject else "",
                    "class_level": lesson.class_level.level_name if lesson.class_level else "",
                    "type":        "lesson",
                    "source":      lesson.source,
                }],
            )
            lesson_count += 1
            self.stdout.write(f"  [+] Lesson: {lesson.title[:60]}")

        self.stdout.write(self.style.SUCCESS(f"\n  {lesson_count} lessons embedded.\n"))

        # ── 4. Embed CurriculumFiles (with real PDF/text content) ───────────────
        qs = CurriculumFile.objects.select_related("subject", "class_level")
        if options.get("only_unindexed") and not options["rebuild"]:
            qs = qs.filter(is_indexed=False)

        file_count = 0
        for cf in qs:
            doc_id = f"file_{cf.id}"

            # Try to extract actual file content
            file_text = self._extract_file_text(cf)
            # Combine extracted text with metadata
            meta_text = f"{cf.title}\n{cf.description}\n{' '.join(cf.tag_list)}"
            text = (file_text or meta_text)[:8000]

            embedding = model.encode(text[:4000]).tolist()
            files_col.upsert(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[text],
                metadatas=[{
                    "title":       cf.title,
                    "file_type":   cf.file_type,
                    "subject":     cf.subject.subject_name if cf.subject else "",
                    "class_level": cf.class_level.level_name if cf.class_level else "",
                    "tags":        cf.tags,
                    "source":      cf.source,
                    "file_id":     str(cf.id),
                    "has_content": bool(file_text),
                }],
            )
            cf.is_indexed = True
            cf.indexed_at = timezone.now()
            cf.save(update_fields=["is_indexed", "indexed_at"])
            file_count += 1
            content_flag = "[PDF text]" if file_text else "[meta only]"
            self.stdout.write(f"  [+] {content_flag} [{cf.file_type}] {cf.title[:55]}")

        self.stdout.write(self.style.SUCCESS(f"\n  {file_count} library files embedded."))
        self.stdout.write(self.style.SUCCESS(
            f"\n[DONE] RAG index built: {lesson_count} lessons + {file_count} files -> {chroma_path}\n"
        ))

    def _extract_file_text(self, cf) -> str:
        """
        Attempt to extract plain text from a CurriculumFile.
        Supports PDF files stored in R2 or locally.
        Returns extracted text or empty string on failure.
        """
        if not cf.file:
            return ""

        try:
            from django.conf import settings
            import io

            file_name = str(cf.file)

            # ── Try reading from R2 via boto3 ──────────────────────────────────
            if getattr(settings, "AWS_ACCESS_KEY_ID", ""):
                import boto3
                s3 = boto3.client(
                    "s3",
                    endpoint_url=settings.AWS_S3_ENDPOINT_URL,
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name="auto",
                )
                obj = s3.get_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=file_name)
                raw = obj["Body"].read()
            else:
                # Local media fallback
                local_path = settings.MEDIA_ROOT / file_name
                if not local_path.exists():
                    return ""
                raw = local_path.read_bytes()

            # ── Extract text based on file type ────────────────────────────────
            if cf.file_type == "PDF" or file_name.lower().endswith(".pdf"):
                from pypdf import PdfReader
                reader = PdfReader(io.BytesIO(raw))
                pages = []
                for page in reader.pages[:30]:   # Max 30 pages
                    pages.append(page.extract_text() or "")
                return "\n".join(pages)

            elif cf.file_type == "IMAGE" or file_name.lower().endswith((".jpg", ".jpeg", ".png")):
                # Images can't be text-extracted here; embedding uses metadata only
                return ""

            else:
                # Try decoding as plain text (HTML, txt, etc.)
                return raw.decode("utf-8", errors="ignore")[:8000]

        except Exception as e:
            self.stdout.write(f"      [warn] Could not extract text from {cf.title}: {e}")
            return ""
