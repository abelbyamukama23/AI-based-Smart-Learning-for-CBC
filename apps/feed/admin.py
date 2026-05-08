from django.contrib import admin
from .models import Post, Comment, Reaction

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('author', 'visibility', 'date_posted', 'is_deleted')
    list_filter = ('visibility', 'is_deleted', 'date_posted')
    search_fields = ('author__username', 'content')
    actions = ['soft_delete', 'restore']

    def soft_delete(self, request, queryset):
        queryset.update(is_deleted=True)
    soft_delete.short_description = "Mark selected posts as deleted"

    def restore(self, request, queryset):
        queryset.update(is_deleted=False)
    restore.short_description = "Restore selected deleted posts"

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'post', 'date_posted')
    search_fields = ('author__username', 'text')

@admin.register(Reaction)
class ReactionAdmin(admin.ModelAdmin):
    list_display = ('learner', 'type', 'post', 'date_reacted')
    list_filter = ('type',)
    search_fields = ('learner__username',)
