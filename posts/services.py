import typing

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db.models import F, QuerySet, Count
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


def get_full_posts_queryset(queryset: QuerySet) -> QuerySet:
    return (queryset.annotate(likes_count=Count("likes"), comments_count=Count("comments"))   # noqa
            .prefetch_related("images").select_related("author"))


def filter_posts_queryset_by_author(request: Request, queryset: QuerySet) -> QuerySet:
    user = request.query_params.get("user", None)
    key = settings.USER_RELATED_CACHE_NAME_SEP + settings.USER_POSTS_CACHE_NAME

    if user and user.isnumeric():   # noqa
        key = user + key
        res_queryset = cache.get(key)
        if not res_queryset:
            user = get_object_or_404(User, pk=int(user))
            res_queryset = get_full_posts_queryset(queryset.filter(author=user).order_by("-id"))
            cache.set(key, res_queryset)
    else:
        key = str(request.user.pk) + key
        res_queryset = cache.get(key)
        if not res_queryset:
            res_queryset = get_full_posts_queryset(queryset.filter(author=request.user).order_by("-id"))
            cache.set(key, res_queryset)

    return res_queryset


def filter_posts_queryset_by_top(request: Request, queryset: QuerySet) -> typing.Tuple[QuerySet, bool]:
    top = request.query_params.get("top", None)

    if top and top == "likes":
        key = settings.POSTS_LIKED_TOP_CACHE_NAME
        res_queryset = cache.get(key)
        if not res_queryset:
            res_queryset = get_full_posts_queryset(queryset.order_by(F("likes_count").desc())[:50])
            cache.set(key, res_queryset)

        return res_queryset, True
    elif top and top == "recent":
        key = settings.POSTS_RELATED_TOP_CACHE_NAME
        res_queryset = cache.get(key)
        if not res_queryset:
            res_queryset = get_full_posts_queryset(queryset.order_by("-id")[:50])
            cache.set(key, res_queryset, 60*60)

        return res_queryset, True

    return queryset, False
