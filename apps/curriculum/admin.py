from django.contrib import admin
from .models import Subject, Level, Competency, Lesson

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
    filter_horizontal = ('competencies',) # nicer widget for ManyToMany
