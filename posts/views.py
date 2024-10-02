from rest_framework import permissions, viewsets, mixins

from posts.permissions import PostPermission
from posts.serializers import PostSerializer


class PostViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = PostSerializer
    permission_classes = (permissions.IsAuthenticated, PostPermission)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
