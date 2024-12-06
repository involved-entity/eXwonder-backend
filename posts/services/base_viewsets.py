from django.shortcuts import get_object_or_404
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.request import Request
from rest_framework.response import Response

from posts.permissions import IsOwnerOrReadOnly
from posts.services.mixins import CreateModelMixin


class BaseLikeViewSet(CreateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    permission_classes = permissions.IsAuthenticated, IsOwnerOrReadOnly
    entity_model = None

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        entity_id = self.kwargs[self.lookup_url_kwarg]
        get_object_or_404(self.entity_model, pk=entity_id).likes.filter(author=request.user).delete()  # noqa
        return Response(status=status.HTTP_204_NO_CONTENT)
