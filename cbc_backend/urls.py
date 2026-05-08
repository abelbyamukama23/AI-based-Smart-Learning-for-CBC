"""
CBC Digital Learning Platform — Root URL Configuration
API versioning via URL namespace: /api/v1/
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Django admin — for MoES content management in later phases
    path("admin/", admin.site.urls),

    # API v1 — all app routes mounted under versioned namespace
    path("api/v1/", include([
        path("auth/",       include("apps.accounts.urls",  namespace="accounts")),
        path("curriculum/", include("apps.curriculum.urls", namespace="curriculum")),
        path("tutor/",      include("apps.ai_tutor.urls",  namespace="ai_tutor")),
        path("feed/",       include("apps.feed.urls",      namespace="feed")),
    ])),
]

admin.site.site_header = "CBC Learning Platform Administration"
admin.site.site_title = "CBC Admin Portal"
admin.site.index_title = "Welcome to CBC Learning Platform Portal"
