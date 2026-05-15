"""
tests/test_feed_service.py
───────────────────────────
Unit & integration tests for the feed Service layer.

Run:
    pytest tests/test_feed_service.py -v
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from apps.feed.exceptions import PostNotFoundError, UnauthorizedPostActionError
from apps.feed.services import CommentService, PostService, ReactionService


# ═══════════════════════════════════════════════════════════════════════════════
# Unit tests — mocked models, no DB
# ═══════════════════════════════════════════════════════════════════════════════

class TestPostServiceUnit:

    @pytest.mark.unit
    def test_soft_delete_raises_for_non_author(self):
        """Only the author can delete a post — others get UnauthorizedPostActionError."""
        author = MagicMock()
        requester = MagicMock()   # A different user

        post = MagicMock()
        post.author = author

        with pytest.raises(UnauthorizedPostActionError):
            PostService.soft_delete(post, requesting_user=requester)

    @pytest.mark.unit
    def test_soft_delete_sets_is_deleted_flag(self):
        """soft_delete sets is_deleted=True and calls save with correct update_fields."""
        user = MagicMock()
        post = MagicMock()
        post.author = user
        post.is_deleted = False

        PostService.soft_delete(post, requesting_user=user)

        assert post.is_deleted is True
        post.save.assert_called_once_with(update_fields=["is_deleted"])


class TestReactionServiceUnit:

    @pytest.mark.unit
    def test_toggle_creates_reaction_when_none_exists(self):
        """toggle() creates a new Reaction and returns action='liked'."""
        post = MagicMock()
        user = MagicMock()

        with patch("apps.feed.services.Reaction") as MockReaction:
            MockReaction.objects.filter.return_value.first.return_value = None

            result = ReactionService.toggle(post, user, reaction_type="LIKE")

        assert result["action"] == "liked"
        assert result["type"] == "LIKE"
        MockReaction.objects.create.assert_called_once()

    @pytest.mark.unit
    def test_toggle_deletes_reaction_when_already_exists(self):
        """toggle() deletes an existing Reaction and returns action='unliked'."""
        post = MagicMock()
        user = MagicMock()
        existing = MagicMock()

        with patch("apps.feed.services.Reaction") as MockReaction:
            MockReaction.objects.filter.return_value.first.return_value = existing

            result = ReactionService.toggle(post, user, reaction_type="LIKE")

        assert result["action"] == "unliked"
        existing.delete.assert_called_once()
        MockReaction.objects.create.assert_not_called()


# ═══════════════════════════════════════════════════════════════════════════════
# Integration tests — uses test DB
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestPostServiceIntegration:

    def _make_user(self, email="alice@test.ug", role="LEARNER"):
        from apps.accounts.models import User
        return User.objects.create_user(
            username=email.split("@")[0],
            email=email,
            password="pass",
            role=role,
        )

    def _make_post(self, author, content="Test post content"):
        from apps.feed.models import Post, Visibility
        return Post.objects.create(
            author=author,
            content=content,
            visibility=Visibility.PUBLIC,
        )

    def test_get_visible_posts_excludes_soft_deleted(self):
        """is_deleted posts never appear in the feed queryset."""
        user = self._make_user()
        post = self._make_post(user)
        post.is_deleted = True
        post.save()

        qs = PostService.get_visible_posts(user)
        assert not qs.filter(pk=post.pk).exists()

    def test_get_visible_posts_includes_own_posts(self):
        """Author sees their own posts regardless of visibility."""
        user = self._make_user()
        post = self._make_post(user)

        qs = PostService.get_visible_posts(user)
        assert qs.filter(pk=post.pk).exists()

    def test_soft_delete_does_not_remove_from_db(self):
        """Soft-deleted posts are hidden from the feed but still in the DB."""
        from apps.feed.models import Post
        user = self._make_user()
        post = self._make_post(user)

        PostService.soft_delete(post, requesting_user=user)

        # Hidden from service queryset
        assert not PostService.get_visible_posts(user).filter(pk=post.pk).exists()
        # Still physically in the DB (soft delete, not hard delete)
        assert Post.objects.filter(pk=post.pk).exists()

    def test_reaction_toggle_is_idempotent(self):
        """Toggling the same reaction twice returns to 0 reactions."""
        from apps.feed.models import Reaction
        user = self._make_user()
        post = self._make_post(user)

        ReactionService.toggle(post, user, "LIKE")
        assert Reaction.objects.filter(post=post, learner=user, type="LIKE").count() == 1

        ReactionService.toggle(post, user, "LIKE")
        assert Reaction.objects.filter(post=post, learner=user, type="LIKE").count() == 0


@pytest.mark.django_db
class TestCommentServiceIntegration:

    def _make_user(self, email="bob@test.ug"):
        from apps.accounts.models import User
        return User.objects.create_user(
            username=email.split("@")[0], email=email, password="pass", role="LEARNER"
        )

    def _make_post(self, author):
        from apps.feed.models import Post, Visibility
        return Post.objects.create(
            author=author, content="Hello", visibility=Visibility.PUBLIC
        )

    def test_create_comment(self):
        """CommentService.create() persists the comment to the DB."""
        from apps.feed.models import Comment
        user = self._make_user()
        post = self._make_post(user)

        comment = CommentService.create(post, author=user, text="Great post!")

        assert Comment.objects.filter(pk=comment.pk).exists()
        assert comment.text == "Great post!"
        assert comment.author == user

    def test_get_for_post_returns_comments_in_order(self):
        """Comments are returned in ascending creation order."""
        user = self._make_user()
        post = self._make_post(user)

        CommentService.create(post, user, "First")
        CommentService.create(post, user, "Second")

        comments = list(CommentService.get_for_post(post))
        assert comments[0].text == "First"
        assert comments[1].text == "Second"
