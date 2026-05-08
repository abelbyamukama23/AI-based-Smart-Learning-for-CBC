import uuid
from django.db import models
from apps.accounts.models import User

class Visibility(models.TextChoices):
    PRIVATE = "PRIVATE", "Private"
    PEERS = "PEERS", "Peers"
    TEACHERS = "TEACHERS", "Teachers"
    PUBLIC = "PUBLIC", "Public"

class ReactionType(models.TextChoices):
    LIKE = "LIKE", "❤️"
    SHARE = "SHARE", "🔃"

class Post(models.Model):
    """
    Learner post/knowledge contribution.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    content = models.TextField()
    photo = models.ImageField(upload_to="feed/photos/", blank=True, null=True, help_text="Optional photo upload")
    video = models.FileField(upload_to="feed/videos/", blank=True, null=True, help_text="Optional video upload")
    video_description = models.TextField(blank=True, help_text="Description for the video")
    visibility = models.CharField(max_length=20, choices=Visibility.choices, default=Visibility.PRIVATE)
    date_posted = models.DateTimeField(auto_now_add=True, db_index=True)
    is_deleted = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ['-date_posted']

    def __str__(self):
        return f"Post by {self.author.username} on {self.date_posted.strftime('%Y-%m-%d')}"

class Comment(models.Model):
    """
    Threaded comment on a post.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="post_comments")
    text = models.TextField()
    date_posted = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['date_posted']

    def __str__(self):
        return f"Comment by {self.author.username} on Post {self.post.id}"

class Reaction(models.Model):
    """
    Learner reaction to a post.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    learner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reactions")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="reactions")
    type = models.CharField(max_length=20, choices=ReactionType.choices, db_index=True)
    date_reacted = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['learner', 'post', 'type'], name='unique_learner_post_reaction')
        ]

    def __str__(self):
        return f"{self.learner.username} {self.type} on Post {self.post.id}"
