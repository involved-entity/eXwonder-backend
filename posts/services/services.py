import typing

import pytz
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db.models import Count, F, Q, QuerySet
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.request import Request

from posts.models import Post, PostImage, Tag

User = get_user_model()


def extract_post_images_from_request_data(post: Post, data: typing.Mapping) -> typing.List[PostImage]:
    post_images = []

    for key, value in data.items():
        if key.startswith("image"):
            instance = PostImage(image=value, post=post)
            if key == "image0":
                post_images.insert(0, instance)
            else:
                post_images.append(instance)

    return post_images


def get_or_create_tags(tags: typing.List[str]) -> QuerySet[Tag]:
    existing_tags = Tag.objects.filter(name__in=tags)  # noqa
    existing_tag_names = set(existing_tags.values_list("name", flat=True))

    new_tags = [Tag(name=name) for name in tags if name not in existing_tag_names]

    Tag.objects.bulk_create(new_tags)  # noqa
    return Tag.objects.filter(name__in=tags)  # noqa


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

    return (
        queryset.annotate(**annotate)
        .prefetch_related(prefix + "images")
        .prefetch_related(prefix + "tags")
        .select_related(prefix + "author")
    )


def get_full_annotated_posts_queryset(
    request: Request, queryset: QuerySet, annotated_field_prefix: typing.Optional[str] = None
) -> QuerySet:
    queryset = annotate_likes_and_comments_count_posts_queryset(queryset, annotated_field_prefix)
    return annotate_with_user_data_posts_queryset(request, queryset, annotated_field_prefix)


def filter_posts_queryset_by_recommended(request: Request, queryset: QuerySet) -> QuerySet:
    liked_tags = (
        request.user.likes.values("post__tags").annotate(tag_count=Count("post__tags")).order_by("-tag_count")[:3]
    )

    tag_ids = [tag["post__tags"] for tag in liked_tags]

    recommended_posts = (
        queryset.filter(tags__id__in=tag_ids)  # noqa
        .annotate(likes_count=Count("likes"))
        .order_by("-likes_count")
    )

    return get_full_annotated_posts_queryset(request, recommended_posts.distinct())


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

    if top and top in {"likes", "recent", "updates", "recommended"}:
        res_queryset = None

        match top:
            case "likes":
                res_queryset = filter_posts_queryset_by_likes(request, queryset)
            case "recent":
                res_queryset = filter_posts_queryset_by_recent(request, queryset)
            case "updates":
                res_queryset = filter_posts_queryset_by_updates(request, queryset)
            case "recommended":
                res_queryset = filter_posts_queryset_by_recommended(request, queryset)

        return res_queryset, True

    return queryset, False
