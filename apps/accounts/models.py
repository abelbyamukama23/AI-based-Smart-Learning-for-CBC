import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class Role(models.TextChoices):
    LEARNER = "LEARNER", _("Learner")
    TEACHER = "TEACHER", _("Teacher")
    ADMIN = "ADMIN", _("Admin")

class ClassLevel(models.TextChoices):
    S1 = "S1", _("S1")
    S2 = "S2", _("S2")
    S3 = "S3", _("S3")
    S4 = "S4", _("S4")
    S5 = "S5", _("S5")
    S6 = "S6", _("S6")

class User(AbstractUser):
    """
    Base User table with UUID primary key.
    Implements Joined Table Inheritance pattern.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(max_length=20, choices=Role.choices, db_index=True)
    email = models.EmailField(_('email address'), unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username'] # AbstractUser requires username by default

    def __str__(self):
        return f"{self.email} ({self.role})"

class School(models.Model):
    """Supporting table for schools."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_name = models.CharField(max_length=200, unique=True)
    region = models.CharField(max_length=100, db_index=True)
    district = models.CharField(max_length=100, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    def __str__(self):
        return self.school_name

class Learner(models.Model):
    """Learner extension table."""
    
    class Methodology(models.TextChoices):
        SOCRATIC = "SOCRATIC", _("Socratic (Questioning)")
        DIRECT = "DIRECT", _("Direct Instruction")
        VISUAL = "VISUAL", _("Visual & Storytelling")
        PROJECT = "PROJECT", _("Project-Based")

    class Language(models.TextChoices):
        ENGLISH = "EN", _("English")
        LUGANDA = "LG", _("Luganda")
        SWAHILI = "SW", _("Swahili")
        RUNYANKOLE = "RN", _("Runyankole")
        
    class Theme(models.TextChoices):
        LIGHT = "LIGHT", _("Light")
        DARK = "DARK", _("Dark")
        SYSTEM = "SYSTEM", _("System")
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='learner_profile')
    school = models.ForeignKey(School, on_delete=models.RESTRICT)
    class_level = models.CharField(max_length=2, choices=ClassLevel.choices, db_index=True)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    
    # Advanced Settings
    preferred_methodology = models.CharField(max_length=20, choices=Methodology.choices, default=Methodology.SOCRATIC)
    preferred_language = models.CharField(max_length=2, choices=Language.choices, default=Language.ENGLISH)
    familiar_region = models.CharField(max_length=100, blank=True, null=True, help_text="Used for localized examples")
    preferred_subjects = models.JSONField(default=list, blank=True, help_text="List of subjects the learner focuses on")
    theme = models.CharField(max_length=10, choices=Theme.choices, default=Theme.SYSTEM)

    def __str__(self):
        return f"Learner: {self.user.email} - {self.class_level}"
