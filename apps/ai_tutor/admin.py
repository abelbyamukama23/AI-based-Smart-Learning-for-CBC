from django.contrib import admin
from .models import AISession


@admin.register(AISession)
class AISessionAdmin(admin.ModelAdmin):
    list_display = (
        "learner",
        "timestamp",
        "llm_provider_used",
        "flagged_out_of_scope",
        "tools_called_count",
        "kb_version",
    )
    list_filter = ("flagged_out_of_scope", "llm_provider_used", "kb_version", "timestamp")
    search_fields = ("learner__username", "learner__email", "query", "response")
    readonly_fields = (
        "id",
        "learner",
        "query",
        "response",
        "flagged_out_of_scope",
        "timestamp",
        "kb_version",
        "context_lesson",
        "tool_calls_log",
        "llm_provider_used",
    )

    @admin.display(description="Tools Called")
    def tools_called_count(self, obj):
        return len(obj.tool_calls_log) if obj.tool_calls_log else 0

    # AI sessions are immutable read-only records
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
