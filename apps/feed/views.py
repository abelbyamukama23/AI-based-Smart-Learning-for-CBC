from django.db.models import Count, Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, BasePermission

from .models import Post, Comment, Reaction, Visibility
from .serializers import PostSerializer, CommentSerializer, ReactSerializer

class IsAuthorOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        # Write permissions are only allowed to the author of the post.
        return obj.author == request.user

class PostViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsAuthorOrReadOnly]
    serializer_class = PostSerializer

    def get_queryset(self):
        user = self.request.user
        # Base annotations
        qs = Post.objects.filter(is_deleted=False).annotate(
            comment_count=Count('comments', distinct=True),
            reaction_count=Count('reactions', distinct=True)
        )
        # Filter visibility
        # Learner can see:
        # 1. Their own posts
        # 2. Posts from others that are PEERS or PUBLIC
        return qs.filter(
            Q(author=user) | 
            Q(visibility__in=[Visibility.PEERS, Visibility.PUBLIC])
        )

    def perform_destroy(self, instance):
        # Soft delete
        instance.is_deleted = True
        instance.save()

    @action(detail=True, methods=['post'], url_path='react')
    def react(self, request, pk=None):
        post = self.get_object()
        serializer = ReactSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reaction_type = serializer.validated_data['type']

        # Toggle logic
        reaction = Reaction.objects.filter(learner=request.user, post=post, type=reaction_type).first()
        if reaction:
            reaction.delete()
            return Response({"action": "unliked", "type": reaction_type})
        else:
            Reaction.objects.create(learner=request.user, post=post, type=reaction_type)
            return Response({"action": "liked", "type": reaction_type}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get', 'post'], url_path='comments')
    def comments(self, request, pk=None):
        post = self.get_object()
        
        if request.method == 'GET':
            comments = post.comments.all()
            serializer = CommentSerializer(comments, many=True)
            return Response(serializer.data)
            
        elif request.method == 'POST':
            serializer = CommentSerializer(data=request.data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save(post=post, author=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
