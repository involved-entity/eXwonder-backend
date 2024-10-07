from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.request import Request
from rest_framework.response import Response

from posts.models import Comment, Like, Post
from posts.permissions import IsOwnerOrReadOnly
from posts.serializers import CommentSerializer, LikeSerializer, PostIDSerializer, PostSerializer
from posts.services import CreateModelCustomMixin, filter_posts_queryset_by_author, filter_posts_queryset_by_top
from users.serializers import DetailedCodeSerializer

User = get_user_model()


@extend_schema_view(
    create=extend_schema(request=PostSerializer, responses={
        status.HTTP_201_CREATED: PostSerializer,
        status.HTTP_400_BAD_REQUEST: DetailedCodeSerializer,
        status.HTTP_403_FORBIDDEN: DetailedCodeSerializer
    }),
    list=extend_schema(request=None, parameters=[
        OpenApiParameter(name="user", description="Author of posts (username). Default is request sender.", type=str),
        OpenApiParameter(name="top", description="Valid values is 'likes' and 'recent'. Filter posts by top. "
                                                 "Cant be used with 'user'.", type=str)
    ], responses={
        status.HTTP_200_OK: PostSerializer,
        status.HTTP_403_FORBIDDEN: DetailedCodeSerializer
    }),
    retrieve=extend_schema(request=None, responses={
        status.HTTP_200_OK: PostSerializer,
        status.HTTP_404_NOT_FOUND: DetailedCodeSerializer
    }),
    destroy=extend_schema(request=None, responses={
        status.HTTP_204_NO_CONTENT: None,
        status.HTTP_403_FORBIDDEN: DetailedCodeSerializer,
        status.HTTP_404_NOT_FOUND: DetailedCodeSerializer
    })
)
class PostViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = PostSerializer
    permission_classes = permissions.IsAuthenticated, IsOwnerOrReadOnly
    lookup_url_kwarg = "id"

    def get_queryset(self):
        queryset = Post.objects.filter()   # noqa
        queryset, has_filtered = filter_posts_queryset_by_top(self.request, queryset)
        if not has_filtered:
            queryset = filter_posts_queryset_by_author(self.request, queryset)
        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
        key = settings.POSTS_RELATED_TOP_CACHE_NAME
        cache.delete(key)

        key = str(self.request.user.pk) + settings.USER_RELATED_CACHE_NAME_SEP + settings.USER_POSTS_CACHE_NAME
        cache.delete(key)


@extend_schema_view(
    create=extend_schema(request=PostIDSerializer, responses={
        status.HTTP_201_CREATED: LikeSerializer,
        status.HTTP_400_BAD_REQUEST: DetailedCodeSerializer,
        status.HTTP_404_NOT_FOUND: DetailedCodeSerializer
    }),
    destroy=extend_schema(request=None, responses={
        status.HTTP_204_NO_CONTENT: None,
        status.HTTP_404_NOT_FOUND: DetailedCodeSerializer
    })
)
class LikeViewSet(
    CreateModelCustomMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = LikeSerializer
    queryset = Like.objects.filter()   # noqa
    permission_classes = permissions.IsAuthenticated, IsOwnerOrReadOnly
    lookup_url_kwarg = "post_id"

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        post_id = self.kwargs[self.lookup_url_kwarg]
        get_object_or_404(Post, pk=post_id).likes.filter(author=request.user).delete()   # noqa
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    create=extend_schema(request=PostIDSerializer, responses={
        status.HTTP_201_CREATED: CommentSerializer,
        status.HTTP_400_BAD_REQUEST: DetailedCodeSerializer,
        status.HTTP_404_NOT_FOUND: DetailedCodeSerializer
    }),
    list=extend_schema(request=None, parameters=[
        OpenApiParameter(name="post_id", description="Post id to get comments.", type=int)
    ], responses={
        status.HTTP_200_OK: CommentSerializer,
        status.HTTP_400_BAD_REQUEST: DetailedCodeSerializer,
        status.HTTP_404_NOT_FOUND: DetailedCodeSerializer
    }),
    destroy=extend_schema(request=None, responses={
        status.HTTP_204_NO_CONTENT: None,
        status.HTTP_403_FORBIDDEN: DetailedCodeSerializer,
        status.HTTP_404_NOT_FOUND: DetailedCodeSerializer
    })
)
class CommentViewSet(
    CreateModelCustomMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = CommentSerializer
    permission_classes = permissions.IsAuthenticated, IsOwnerOrReadOnly
    lookup_url_kwarg = "id"

    def get_queryset(self):
        if self.action == "list":
            serializer = PostIDSerializer(data=self.request.query_params)
            serializer.is_valid(raise_exception=True)
            return get_object_or_404(Post, pk=serializer.validated_data["post_id"]).comments.filter()  # noqa
        elif self.action == "destroy":
            return Comment.objects.filter()   # noqa
