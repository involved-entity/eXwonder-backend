import typing

import pytz
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db.models import Count, F, Q, QuerySet
from django.shortcuts import get_object_or_404
from django.utils import timezone
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


def get_full_posts_queryset(request: Request, queryset: QuerySet) -> QuerySet:
    return (queryset
            .annotate(likes_count=Count("likes", distinct=True),
                      comments_count=Count("comments", distinct=True),
                      is_liked=Count("likes", distinct=True, filter=Q(likes__author=request.user)),
                      is_commented=Count("comments", distinct=True, filter=Q(comments__author=request.user)))
            .prefetch_related("images").select_related("author"))


def filter_posts_queryset_by_updates(request: Request, queryset: QuerySet) -> QuerySet:
    key = str(request.user.pk) + settings.USER_RELATED_CACHE_NAME_SEP + settings.USER_UPDATES_CACHE_NAME
    res_queryset = cache.get(key)
    if res_queryset is None:
        res_queryset = queryset.filter(
            author__in=(following.following for following in request.user.following.select_related("following")),
            time_added__lt=timezone.now().replace(tzinfo=pytz.utc),
        )
        if request.user.penultimate_login:
            res_queryset = res_queryset.filter(time_added__gt=request.user.penultimate_login)

        res_queryset = get_full_posts_queryset(request, res_queryset.order_by("-id"))
        cache.set(key, res_queryset, settings.USER_UPDATES_CACHE_TIME)

    return res_queryset


def filter_posts_queryset_by_recent(request: Request, queryset: QuerySet) -> QuerySet:
    key = settings.POSTS_RECENT_TOP_CACHE_NAME
    res_queryset = cache.get(key)
    if not res_queryset:
        res_queryset = get_full_posts_queryset(request, queryset.order_by("-id")[:50])
        cache.set(key, res_queryset, settings.POSTS_RECENT_TOP_CACHE_TIME)
    return res_queryset


def filter_posts_queryset_by_likes(request: Request, queryset):
    key = settings.POSTS_LIKED_TOP_CACHE_NAME
    res_queryset = cache.get(key)
    if not res_queryset:
        res_queryset = get_full_posts_queryset(request, queryset.order_by(F("likes_count").desc())[:50])
        cache.set(key, res_queryset)
    return res_queryset


def filter_posts_queryset_by_author(request: Request, queryset: QuerySet, user: typing.Optional[User] = None) \
        -> QuerySet:
    if user:
        user = get_object_or_404(User, username=user)
        res_queryset = get_full_posts_queryset(request, queryset.filter(author=user).order_by("-id"))
    else:
        res_queryset = get_full_posts_queryset(request, queryset.filter(author=request.user).order_by("-id"))

    return res_queryset


def filter_posts_queryset_by_top(request: Request, queryset: QuerySet) -> typing.Tuple[QuerySet, bool]:
    top = request.query_params.get("top", None)

    if top and top in ("likes", "recent", "updates"):
        res_queryset = filter_posts_queryset_by_likes(request, queryset) if top == "likes" else (
            filter_posts_queryset_by_recent(request, queryset) if top == "recent" else (
                filter_posts_queryset_by_updates(request, queryset)
            )
        )

        return res_queryset, True

    return queryset, False
