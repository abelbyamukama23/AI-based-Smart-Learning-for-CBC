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
