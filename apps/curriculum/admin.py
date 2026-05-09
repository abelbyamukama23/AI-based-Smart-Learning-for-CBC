from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from .models import Subject, Level, Competency, Lesson, CurriculumFile, ResearchEntry


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('subject_name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('subject_name',)


@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ('level_name', 'sort_order')
    ordering = ('sort_order',)


@admin.register(Competency)
class CompetencyAdmin(admin.ModelAdmin):
    list_display = ('competency_name', 'subject', 'level')
    list_filter = ('subject', 'level')
    search_fields = ('competency_name', 'description')


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'class_level', 'source', 'is_downloadable', 'created_at')
    list_filter = ('subject', 'class_level', 'source', 'is_downloadable')
    search_fields = ('title', 'description')
    filter_horizontal = ('competencies',)


# ── Library Agent Admin ────────────────────────────────────────────────────────

@admin.register(CurriculumFile)
class CurriculumFileAdmin(admin.ModelAdmin):
    list_display  = ('title', 'file_type', 'subject', 'class_level', 'source', 'index_status', 'created_at')
    list_filter   = ('file_type', 'subject', 'class_level', 'is_indexed')
    search_fields = ('title', 'description', 'tags')
    readonly_fields = ('is_indexed', 'indexed_at', 'created_at', 'modified_at')
    fieldsets = (
        ('File Details', {
            'fields': ('title', 'description', 'file', 'file_type', 'source', 'tags')
        }),
        ('Curriculum Mapping', {
            'fields': ('subject', 'class_level')
        }),
        ('RAG Index Status', {
            'fields': ('is_indexed', 'indexed_at'),
            'description': 'Run python manage.py build_library_index to embed new files.',
            'classes': ('collapse',),
        }),
        ('Metadata', {
            'fields': ('uploaded_by', 'created_at', 'modified_at'),
            'classes': ('collapse',),
        }),
    )

    def index_status(self, obj):
        if obj.is_indexed:
            return format_html('<span style="color:green;">✔ Indexed</span>')
        return format_html('<span style="color:orange;">⏳ Pending</span>')
    index_status.short_description = 'RAG Index'

    def save_model(self, request, obj, form, change):
        if not obj.uploaded_by_id:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ResearchEntry)
class ResearchEntryAdmin(admin.ModelAdmin):
    list_display   = ('topic', 'subject', 'relevance_badge', 'status', 'auto_approved', 'created_at')
    list_filter    = ('status', 'subject', 'class_level', 'auto_approved')
    search_fields  = ('topic', 'title', 'source_url', 'content')
    readonly_fields = ('relevance_score', 'auto_approved', 'created_at', 'reviewed_at', 'library_file')
    actions        = ['approve_entries', 'reject_entries']

    def relevance_badge(self, obj):
        score = obj.relevance_score
        color = 'green' if score >= 0.8 else ('orange' if score >= 0.5 else 'red')
        return format_html('<span style="color:{};">{:.0%}</span>', color, score)
    relevance_badge.short_description = 'Relevance'

    def approve_entries(self, request, queryset):
        from django.utils import timezone
        updated = 0
        for entry in queryset.filter(status=ResearchEntry.Status.PENDING):
            entry.status = ResearchEntry.Status.APPROVED
            entry.reviewed_at = timezone.now()
            entry.save()
            updated += 1
        self.message_user(request, f"{updated} entries approved and queued for indexing.")
    approve_entries.short_description = "✔ Approve selected entries"

    def reject_entries(self, request, queryset):
        updated = queryset.filter(status=ResearchEntry.Status.PENDING).update(
            status=ResearchEntry.Status.REJECTED,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f"{updated} entries rejected.")
    reject_entries.short_description = "✘ Reject selected entries"
