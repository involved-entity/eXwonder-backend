import typing

import pytz
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db.models import Count, F, Q, QuerySet
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import mixins, serializers, status
from rest_framework.request import Request
from rest_framework.response import Response

from posts.models import Post

User = get_user_model()


class CreateModelCustomMixin(mixins.CreateModelMixin):
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
        entity_pk = self.__get_and_validate_post_id(request)
        serializer = self.get_serializer(data=request.data)  # noqa
        serializer.is_valid(raise_exception=True)
        serializer.save(
            **{self.author_field: request.user},
            **{self.entity_field: get_object_or_404(self.entity_model, pk=entity_pk)},
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)


def annotate_likes_count_and_is_liked_comments_queryset(request: Request, queryset: QuerySet) -> QuerySet:
    annotate = {
        "likes_count": Count("likes", distinct=True),
        "is_liked": Count("likes", distinct=True, filter=Q(likes__author=request.user)),
    }
    return queryset.annotate(**annotate).order_by("-likes_count", "-time_added")


def annotate_with_user_data_posts_queryset(
    request: Request, queryset: QuerySet, annotated_field_prefix: typing.Optional[str] = None
) -> QuerySet:
    prefix = f"{annotated_field_prefix}__" if annotated_field_prefix else ""

    annotate = {
        "is_liked": (Count(prefix + "likes", distinct=True, filter=Q(**{prefix + "likes__author": request.user}))),
        "is_commented": (
            Count(prefix + "comments", distinct=True, filter=Q(**{prefix + "comments__author": request.user}))
        ),
        "is_saved": (Count(prefix + "saved_by", distinct=True, filter=Q(**{prefix + "saved_by__owner": request.user}))),
    }
    return queryset.annotate(**annotate)


def annotate_likes_and_comments_count_posts_queryset(
    queryset: QuerySet, annotated_field_prefix: typing.Optional[str] = None
) -> QuerySet:
    prefix = f"{annotated_field_prefix}__" if annotated_field_prefix else ""

    annotate = {
        "likes_count": Count(prefix + "likes", distinct=True),
        "comments_count": Count(prefix + "comments", distinct=True),
    }

    return queryset.annotate(**annotate).prefetch_related(prefix + "images").select_related(prefix + "author")


def get_full_annotated_posts_queryset(
    request: Request, queryset: QuerySet, annotated_field_prefix: typing.Optional[str] = None
) -> QuerySet:
    queryset = annotate_likes_and_comments_count_posts_queryset(queryset, annotated_field_prefix)
    return annotate_with_user_data_posts_queryset(request, queryset, annotated_field_prefix)


def filter_posts_queryset_by_updates(request: Request, queryset: QuerySet) -> QuerySet:
    res_queryset = queryset.filter(
        author__in=(following.following for following in request.user.following.select_related("following")),
        time_added__lt=timezone.now().replace(tzinfo=pytz.utc),
    )
    if request.user.penultimate_login:
        res_queryset = res_queryset.filter(time_added__gt=request.user.penultimate_login)

    return get_full_annotated_posts_queryset(request, res_queryset.order_by("-id"))


def filter_posts_queryset_by_recent(request: Request, queryset: QuerySet) -> QuerySet:
    key = settings.POSTS_RECENT_TOP_CACHE_NAME
    res_queryset = cache.get(key)
    if not res_queryset:
        res_queryset = annotate_likes_and_comments_count_posts_queryset(queryset.order_by("-id")[:50])
        cache.set(key, res_queryset, settings.POSTS_RECENT_TOP_CACHE_TIME)
    res_queryset = annotate_with_user_data_posts_queryset(request, res_queryset)
    return res_queryset


def filter_posts_queryset_by_likes(request: Request, queryset):
    key = settings.POSTS_LIKED_TOP_CACHE_NAME
    res_queryset = cache.get(key)
    if not res_queryset:
        res_queryset = annotate_likes_and_comments_count_posts_queryset(queryset.order_by(F("likes_count").desc())[:50])
        cache.set(key, res_queryset)
    res_queryset = annotate_with_user_data_posts_queryset(request, res_queryset)
    return res_queryset


def filter_posts_queryset_by_author(
    request: Request, queryset: QuerySet, user: typing.Optional[User] = None
) -> QuerySet:
    if user:
        user = get_object_or_404(User, username=user)
        res_queryset = get_full_annotated_posts_queryset(request, queryset.filter(author=user).order_by("-id"))
    else:
        res_queryset = get_full_annotated_posts_queryset(request, queryset.filter(author=request.user).order_by("-id"))

    return res_queryset


def filter_posts_queryset_by_top(request: Request, queryset: QuerySet) -> typing.Tuple[QuerySet, bool]:
    top = request.query_params.get("top", None)

    if top and top in ("likes", "recent", "updates"):
        res_queryset = (
            filter_posts_queryset_by_likes(request, queryset)
            if top == "likes"
            else (
                filter_posts_queryset_by_recent(request, queryset)
                if top == "recent"
                else (filter_posts_queryset_by_updates(request, queryset))
            )
        )

        return res_queryset, True

    return queryset, False
