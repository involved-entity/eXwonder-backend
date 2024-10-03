from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.request import Request
from rest_framework.response import Response

from posts.models import Post
from posts.permissions import PostPermission
from posts.serializers import LikeSerializer, PostSerializer

User = get_user_model()


class PostViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = PostSerializer
    permission_classes = (permissions.IsAuthenticated, PostPermission)
    lookup_url_kwarg = "id"

    def get_queryset(self):
        user = self.request.query_params.get("user", 0)
        user = get_object_or_404(User, pk=int(user)) if user and user.isnumeric() else self.request.user
        return user.posts.filter()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class LikeViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = LikeSerializer
    permission_classes = permissions.IsAuthenticated,
    lookup_url_kwarg = "id"

    def create(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        post_id = self.request.data.get(self.lookup_url_kwarg, 0)
        if post_id and post_id.isnumeric():
            serializer.save(
                author=self.request.user,
                post=get_object_or_404(Post, pk=post_id)
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(status=status.HTTP_400_BAD_REQUEST)
