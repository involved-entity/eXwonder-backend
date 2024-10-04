import typing

from django.contrib.auth import get_user_model
from django.db.models import F, QuerySet
from django.shortcuts import get_object_or_404
from rest_framework import mixins, status
from rest_framework.request import Request
from rest_framework.response import Response

from posts.models import Post
from posts.serializers import PostIDSerializer

User = get_user_model()


class CreateModelCustomMixin(mixins.CreateModelMixin):
    def __get_and_validate_post_id(self, request: Request) -> int:
        serializer = PostIDSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data["post_id"]

    def create(self, request: Request, *args, **kwargs) -> Response:
        post_id = self.__get_and_validate_post_id(request)
        serializer = self.get_serializer(data=request.data)   # noqa
        serializer.is_valid(raise_exception=True)
        serializer.save(
            author=request.user,
            post=get_object_or_404(Post, pk=post_id)
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)


def filter_posts_queryset_by_author(request: Request, queryset: QuerySet) -> QuerySet:
    user = request.query_params.get("user", None)
    if user and user.isnumeric():   # noqa
        return queryset.filter(author=get_object_or_404(User, pk=int(user)))
    else:
        return queryset.filter(author=request.user)


def filter_posts_queryset_by_top(request: Request, queryset: QuerySet) -> typing.Tuple[QuerySet, bool]:
    top = request.query_params.get("top", None)
    if top and top == "likes":
        return queryset.filter(F("likes_count").desc())[:50], True
    elif top and top == "recent":
        return queryset[:50], True
    return queryset, False
