from rest_framework import serializers
from apps.accounts.serializers import UserSerializer
from .models import Post, Comment, Reaction, Visibility, ReactionType

class CommentSerializer(serializers.ModelSerializer):
    author_detail = UserSerializer(source='author', read_only=True)
    
    class Meta:
        model = Comment
        fields = ['id', 'author', 'author_detail', 'text', 'date_posted']
        read_only_fields = ['id', 'author', 'date_posted']

class PostSerializer(serializers.ModelSerializer):
    author_detail = UserSerializer(source='author', read_only=True)
    comment_count = serializers.IntegerField(read_only=True)
    reaction_count = serializers.IntegerField(read_only=True)
    # Exposing the comments for embedded view is optional, limiting to list via action per design
    
    class Meta:
        model = Post
        fields = ['id', 'author', 'author_detail', 'content', 'photo', 'video', 'video_description', 'visibility', 'date_posted', 'comment_count', 'reaction_count']
        read_only_fields = ['id', 'author', 'date_posted', 'comment_count', 'reaction_count']

    def create(self, validated_data):
        # Automatically set author to the current user
        request = self.context.get('request')
        validated_data['author'] = request.user
        return super().create(validated_data)

class ReactSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=ReactionType.choices)
