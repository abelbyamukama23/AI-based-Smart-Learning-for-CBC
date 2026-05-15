"""
apps/feed/views.py
───────────────────
HTTP adapters only — business logic delegated to feed/services.py.

Design Patterns:
  • Service Layer   — visibility, soft-delete, toggle-reaction logic in PostService.
  • Thin Controller — each view method is ≤ 10 lines of HTTP glue.
"""

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.response import Response

from .models import Post
from .serializers import CommentSerializer, PostSerializer, ReactSerializer
from .services import CommentService, PostService, ReactionService


class IsAuthorOrReadOnly(BasePermission):
    """Object-level permission: only the post author can mutate their post."""

    def has_object_permission(self, request, view, obj):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        return obj.author == request.user


class PostViewSet(viewsets.ModelViewSet):
    """
    CRUD for posts.  Visibility filtering and soft-delete handled by PostService.
    """
    permission_classes = [IsAuthenticated, IsAuthorOrReadOnly]
    serializer_class = PostSerializer

    def get_queryset(self):
        return PostService.get_visible_posts(self.request.user)

    def perform_destroy(self, instance):
        PostService.soft_delete(instance, self.request.user)

    @action(detail=True, methods=["post"], url_path="react")
    def react(self, request, pk=None):
        post = self.get_object()
        serializer = ReactSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = ReactionService.toggle(
            post, request.user, serializer.validated_data["type"]
        )
        http_status = (
            status.HTTP_201_CREATED if result["action"] == "liked"
            else status.HTTP_200_OK
        )
        return Response(result, status=http_status)

    @action(detail=True, methods=["get", "post"], url_path="comments")
    def comments(self, request, pk=None):
        post = self.get_object()

        if request.method == "GET":
            comments = CommentService.get_for_post(post)
            return Response(CommentSerializer(comments, many=True).data)

        serializer = CommentSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        comment = CommentService.create(post, request.user, serializer.validated_data["text"])
        return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)
