import uuid
from django.db import models
from apps.accounts.models import ClassLevel

class ContentType(models.TextChoices):
    LESSON = "LESSON", "Lesson"
    MATERIAL = "MATERIAL", "Material"

class Subject(models.Model):
    """Official CBC Subject"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subject_name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True, db_index=True)

    def __str__(self):
        return self.subject_name

class Level(models.Model):
    """Class Level definitions. Instead of enum, an explicit table."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    level_name = models.CharField(max_length=2, choices=ClassLevel.choices, unique=True)
    sort_order = models.SmallIntegerField(db_index=True)

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return self.level_name

class Competency(models.Model):
    """Official CBC Competency, mapped to a subject and class level"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="competencies")
    level = models.ForeignKey(Level, on_delete=models.CASCADE, related_name="competencies")
    competency_name = models.CharField(max_length=200, db_index=True)
    description = models.TextField()

    def __str__(self):
        return f"{self.subject} ({self.level}) - {self.competency_name}"

class Content(models.Model):
    """
    Abstract base for Content hierarchy.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, db_index=True)
    description = models.TextField()
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="%(class)ss")
    class_level = models.ForeignKey(Level, on_delete=models.CASCADE, related_name="%(class)ss")
    competencies = models.ManyToManyField(Competency, related_name="%(class)ss")
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    content_type = models.CharField(max_length=20, choices=ContentType.choices, db_index=True)

    class Meta:
        abstract = True

class Lesson(Content):
    """Concrete Lesson Content"""
    source = models.CharField(max_length=50, default="NCDC")
    is_downloadable = models.BooleanField(default=True, db_index=True)
    file_size_kb = models.IntegerField(null=True, blank=True)
    body_html = models.TextField(blank=True, help_text="Supporting text content")
    image = models.ImageField(upload_to="curriculum/images/", blank=True, null=True, help_text="Supporting image for the lesson")
    video_url = models.URLField(max_length=500, blank=True, null=True, help_text="Link to video content")
    video_file = models.FileField(upload_to="curriculum/videos/", blank=True, null=True, help_text="Direct video upload")

    def save(self, *args, **kwargs):
        self.content_type = ContentType.LESSON
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Lesson: {self.title} ({self.subject} - {self.class_level})"


# ── Library Agent Models ──────────────────────────────────────────────────────

class FileType(models.TextChoices):
    PDF       = "PDF",   "PDF / Textbook"
    IMAGE     = "IMAGE", "Image / Illustration"
    AUDIO     = "AUDIO", "Audio Recording"
    MAP       = "MAP",   "Map / Geography"
    VIDEO     = "VIDEO", "Video"
    OTHER     = "OTHER", "Other"


class CurriculumFile(models.Model):
    """
    A library asset stored in Cloudflare R2.
    Represents textbooks, maps, audio, images, and other teaching materials.
    The Library Agent searches and compiles lessons from these.
    """
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title       = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True)
    file_type   = models.CharField(max_length=10, choices=FileType.choices, db_index=True)
    file        = models.FileField(upload_to="library/", help_text="Uploaded to Cloudflare R2")
    subject     = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, blank=True, related_name="library_files")
    class_level = models.ForeignKey(Level, on_delete=models.SET_NULL, null=True, blank=True, related_name="library_files")
    tags        = models.CharField(max_length=500, blank=True, help_text="Comma-separated topic tags")
    # RAG indexing status
    is_indexed  = models.BooleanField(default=False, help_text="True after ChromaDB embedding is built")
    indexed_at  = models.DateTimeField(null=True, blank=True)
    # Metadata
    source      = models.CharField(max_length=200, blank=True, help_text="Publisher, NCDC, etc.")
    uploaded_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="uploaded_files"
    )
    created_at  = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Library File"
        verbose_name_plural = "Library Files"

    def __str__(self):
        return f"[{self.file_type}] {self.title}"

    @property
    def tag_list(self):
        return [t.strip() for t in self.tags.split(",") if t.strip()]


class ResearchEntry(models.Model):
    """
    Content discovered by the Research Agent from external web sources.
    Goes through an approval workflow before entering the main library.
    """
    class Status(models.TextChoices):
        PENDING  = "PENDING",  "Pending Review"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    topic            = models.CharField(max_length=255)
    source_url       = models.URLField(max_length=500)
    title            = models.CharField(max_length=255, blank=True)
    content          = models.TextField(help_text="Scraped/summarised content from the web")
    subject          = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, blank=True)
    class_level      = models.ForeignKey(Level, on_delete=models.SET_NULL, null=True, blank=True)
    relevance_score  = models.FloatField(default=0.0, help_text="0.0–1.0 CBC relevance score from LLM")
    status           = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING, db_index=True)
    auto_approved    = models.BooleanField(default=False, help_text="True if auto-approved by relevance threshold")
    # Link to the library file created when approved
    library_file     = models.OneToOneField(
        CurriculumFile, on_delete=models.SET_NULL, null=True, blank=True, related_name="research_source"
    )
    created_at       = models.DateTimeField(auto_now_add=True)
    reviewed_at      = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-relevance_score", "-created_at"]
        verbose_name = "Research Entry"
        verbose_name_plural = "Research Entries"

    def __str__(self):
        return f"[{self.status}] {self.topic} ({self.relevance_score:.2f})"

# ── Knowledge Graph Models ────────────────────────────────────────────────────

class NodeType(models.TextChoices):
    SUBJECT    = "SUBJECT",    "Subject"
    COMPETENCY = "COMPETENCY", "Competency"
    LESSON     = "LESSON",     "Lesson"
    CONCEPT    = "CONCEPT",    "Concept"

class CurriculumNode(models.Model):
    """
    A node in the Curriculum Knowledge Graph.
    Can represent a Subject, Competency, Lesson, or an abstract Concept.
    """
    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    node_type     = models.CharField(max_length=20, choices=NodeType.choices, db_index=True)
    name          = models.CharField(max_length=255, db_index=True)
    description   = models.TextField(blank=True)
    chroma_doc_id = models.CharField(max_length=255, null=True, blank=True, help_text="Links to ChromaDB vector document")
    created_at    = models.DateTimeField(auto_now_add=True)
    modified_at   = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Curriculum Node"
        verbose_name_plural = "Curriculum Nodes"

    def __str__(self):
        return f"[{self.node_type}] {self.name}"

class EdgeType(models.TextChoices):
    REQUIRES   = "REQUIRES",   "Requires / Prerequisite"
    BELONGS_TO = "BELONGS_TO", "Belongs To"
    TEACHES    = "TEACHES",    "Teaches"
    RELATES_TO = "RELATES_TO", "Relates To"

class CurriculumEdge(models.Model):
    """
    A directed relationship between two nodes in the Knowledge Graph.
    """
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source       = models.ForeignKey(CurriculumNode, on_delete=models.CASCADE, related_name='outgoing_edges')
    target       = models.ForeignKey(CurriculumNode, on_delete=models.CASCADE, related_name='incoming_edges')
    relationship = models.CharField(max_length=20, choices=EdgeType.choices, db_index=True)
    weight       = models.FloatField(default=1.0, help_text="Strength or importance of this relationship")
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('source', 'target', 'relationship')
        verbose_name = "Curriculum Edge"
        verbose_name_plural = "Curriculum Edges"

    def __str__(self):
        return f"{self.source.name} --[{self.relationship}]--> {self.target.name}"
