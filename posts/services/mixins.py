from django.shortcuts import get_object_or_404
from rest_framework import mixins, serializers, status
from rest_framework.request import Request
from rest_framework.response import Response

from posts.models import Post


class CreateModelMixin(mixins.CreateModelMixin):
    author_field = "author"
    entity_model = Post
    entity_field = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.entity_field = self.entity_model.__name__.lower()

    def __get_and_validate_post_id(self, request: Request) -> int:
        if (not request.data.get(f"{self.entity_field}_id")) or (int(request.data.get(f"{self.entity_field}_id")) < 1):
            raise serializers.ValidationError()
        return request.data[f"{self.entity_field}_id"]

    def create(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)  # noqa
        serializer.is_valid(raise_exception=True)
        self.perform_create(request, serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, request: Request, serializer: serializers.ModelSerializer) -> None:  # noqa
        entity_pk = self.__get_and_validate_post_id(request)
        serializer.save(
            **{self.author_field: request.user},
            **{self.entity_field: get_object_or_404(self.entity_model, pk=entity_pk)},
        )
