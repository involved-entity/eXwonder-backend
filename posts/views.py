from rest_framework import permissions, viewsets, mixins
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from posts.permissions import PostPermission
from posts.serializers import PostSerializer

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

    def get_queryset(self):
        user = self.request.query_params.get("user", 0)
        user = get_object_or_404(User, pk=int(user)) if user and user.isnumeric() else self.request.user
        return user.posts.filter()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
