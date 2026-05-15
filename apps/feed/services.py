"""
apps/feed/services.py
──────────────────────
Service Layer for the feed domain.

Design Patterns applied:
  • Service Layer — all feed business rules live here
  • SRP           — PostService, CommentService, ReactionService each have one responsibility

Visibility logic, soft-delete logic, and toggle-reaction logic are no longer
inline in view methods — views are pure HTTP adapters.
"""

from __future__ import annotations

from django.db.models import Count, Q

from .exceptions import PostNotFoundError, UnauthorizedPostActionError
from .models import Comment, Post, Reaction, ReactionType, Visibility


class PostService:
    """Business rules for creating, retrieving, and soft-deleting posts."""

    @staticmethod
    def get_visible_posts(user):
        """
        Returns the QuerySet of posts visible to the requesting user.

        Visibility rules:
          - A user always sees their own posts (any visibility setting).
          - A user sees others' posts only when visibility is PEERS or PUBLIC.

        Annotations (comment_count, reaction_count) are added here so views
        never need to re-derive them.
        """
        return (
            Post.objects
            .filter(is_deleted=False)
            .annotate(
                comment_count=Count("comments", distinct=True),
                reaction_count=Count("reactions", distinct=True),
            )
            .filter(
                Q(author=user)
                | Q(visibility__in=[Visibility.PEERS, Visibility.PUBLIC])
            )
            .select_related("author")
        )

    @staticmethod
    def soft_delete(post: Post, requesting_user) -> None:
        """
        Soft-deletes a post.

        Raises:
            UnauthorizedPostActionError if the requesting user is not the author.
        """
        if post.author != requesting_user:
            raise UnauthorizedPostActionError(
                "Only the post author can delete this post."
            )
        post.is_deleted = True
        post.save(update_fields=["is_deleted"])


class ReactionService:
    """Business rules for post reactions (toggle pattern)."""

    @staticmethod
    def toggle(post: Post, user, reaction_type: str) -> dict:
        """
        Toggle a reaction on a post.

        Returns:
            {"action": "liked"|"unliked", "type": reaction_type}
        """
        existing = Reaction.objects.filter(
            learner=user, post=post, type=reaction_type
        ).first()

        if existing:
            existing.delete()
            return {"action": "unliked", "type": reaction_type}

        Reaction.objects.create(learner=user, post=post, type=reaction_type)
        return {"action": "liked", "type": reaction_type}


class CommentService:
    """Business rules for post comments."""

    @staticmethod
    def get_for_post(post: Post):
        """Returns all comments for a post, ordered by date (ascending)."""
        return post.comments.select_related("author").all()

    @staticmethod
    def create(post: Post, author, text: str) -> Comment:
        """Creates and returns a new comment."""
        return Comment.objects.create(post=post, author=author, text=text)
