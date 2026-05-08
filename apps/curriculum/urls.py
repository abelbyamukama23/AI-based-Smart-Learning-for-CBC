from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SubjectViewSet, LevelViewSet, LessonViewSet

app_name = "curriculum"

router = DefaultRouter()
router.register(r'subjects', SubjectViewSet, basename='subject')
router.register(r'class-levels', LevelViewSet, basename='class-level')
router.register(r'lessons', LessonViewSet, basename='lesson')

urlpatterns = [
    path('', include(router.urls)),
]
