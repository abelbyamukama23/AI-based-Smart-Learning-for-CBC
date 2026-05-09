from django.urls import path
from .views import AskViewSet, ChatThreadViewSet

app_name = "ai_tutor"

urlpatterns = [
    # Ask Mwalimu (SSE streaming)
    path("ask/", AskViewSet.as_view({"post": "create"}), name="ask"),

    # Thread list (sidebar)
    path("threads/", ChatThreadViewSet.as_view({"get": "list"}), name="thread_list"),

    # Full thread with all interactions
    path("threads/<uuid:pk>/", ChatThreadViewSet.as_view({"get": "retrieve"}), name="thread_detail"),
]
