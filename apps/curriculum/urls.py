from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SubjectViewSet, LevelViewSet, LessonViewSet, CurriculumFileViewSet

app_name = "curriculum"

router = DefaultRouter()
router.register(r'subjects',     SubjectViewSet,      basename='subject')
router.register(r'class-levels', LevelViewSet,        basename='class-level')
router.register(r'lessons',      LessonViewSet,       basename='lesson')
router.register(r'library',      CurriculumFileViewSet, basename='library')

urlpatterns = [
    path('', include(router.urls)),
]
