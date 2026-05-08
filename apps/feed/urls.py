from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PostViewSet

app_name = "feed"

router = DefaultRouter()
router.register(r'posts', PostViewSet, basename='post')

urlpatterns = [
    path('', include(router.urls)),
]
