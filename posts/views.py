from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.request import Request
from rest_framework.response import Response

from posts.models import Post, Like, Comment
from posts.services import CreateModelCustomMixin
from posts.permissions import IsOwnerOrReadOnly
from posts.serializers import LikeSerializer, PostSerializer, CommentSerializer

User = get_user_model()


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
        user = self.request.query_params.get("user", 0)
        user = get_object_or_404(User, pk=int(user)) if user and user.isnumeric() else self.request.user
        return user.posts.filter()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class LikeViewSet(
    CreateModelCustomMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = LikeSerializer
    queryset = Like.objects.filter()   # noqa
    permission_classes = permissions.IsAuthenticated, IsOwnerOrReadOnly
    lookup_url_kwarg = "post_id"

    def retrieve(self, request: Request, *args, **kwargs) -> Response:
        post_id = self.kwargs[self.lookup_url_kwarg]
        return Response({
            "count": Post.objects.get(pk=post_id).likes.count()   # noqa
        }, status=status.HTTP_200_OK)

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        post_id = self.kwargs[self.lookup_url_kwarg]
        Post.objects.get(pk=post_id).likes.filter(author=request.user).delete()   # noqa
        return Response(status=status.HTTP_204_NO_CONTENT)


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
        if self.request.data.get("post_id", 0) and self.request.data.get("post_id", 0).isnumeric():
            return get_object_or_404(Post, pk=self.request.data["post_id"]).comments.filter()   # noqa
        return Comment.objects.filter()   # noqa
