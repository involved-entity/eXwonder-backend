from django.contrib import admin

from posts.models import Comment, CommentLike, Post, PostImage, PostLike, Saved


class SignatureFilter(admin.SimpleListFilter):
    title = "has signature"
    parameter_name = "signature_exists"

    def lookups(self, request, model_admin):
        return (
            ("true", "Yes"),
            ("false", "No"),
        )

    def queryset(self, request, queryset):
        if self.value() == "true":
            return queryset.filter(signature__gt="")
        elif self.value() == "false":
            return queryset.filter(signature="")
        return queryset


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = "id", "author", "signature_short", "time_added"
    list_display_links = "id", "author"
    ordering = ("-time_added",)
    list_per_page = 50
    search_fields = "id__startswith", "author__username", "signature"
    list_filter = (SignatureFilter,)

    @admin.display(description="Signature", ordering="signature")
    def signature_short(self, post: Post) -> str:
        return post.signature if len(post.signature) < 50 else f"{post.signature[:50]}..."


@admin.register(PostImage)
class PostImageAdmin(admin.ModelAdmin):
    list_display = "id", "image", "post__id"
    ordering = ("-post__time_added",)
    list_per_page = 50
    search_fields = "post__author", "post__signature"


@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    list_per_page = 50
    list_display = "id", "author__username", "post__id"
    list_display_links = "id", "author__username"
    ordering = ("-post__time_added",)
    search_fields = "author__username", "post__id"


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_per_page = 50
    list_display = "id", "author__username", "post__id", "comment_short", "time_added"
    list_display_links = "id", "author__username"
    ordering = ("-time_added",)
    search_fields = "author__username", "post__id"

    @admin.display(description="Comment", ordering="comment")
    def comment_short(self, comment: Comment) -> str:
        return comment.comment if len(comment.comment) < 50 else f"{comment.comment[:50]}..."


@admin.register(CommentLike)
class CommentLikeAdmin(admin.ModelAdmin):
    list_per_page = 50
    list_display = "id", "author__username", "comment__id"
    list_display_links = "id", "author__username"
    ordering = ("-comment__time_added",)
    search_fields = "author__username", "comment__id"


@admin.register(Saved)
class SavedAdmin(admin.ModelAdmin):
    list_per_page = 50
    list_display = "id", "owner__username", "post__id", "time_added"
    list_display_links = "id", "owner__username"
    ordering = ("-time_added",)
    search_fields = "owner__username", "post__id"
