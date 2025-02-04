import pytz
from django.contrib.auth import get_user_model
from django.contrib.sessions.backends.db import SessionStore
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import generics, mixins, permissions, status, views, viewsets
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from users.models import Follow
from users.permissions import UserPermission
from users.serializers import (
    DetailedCodeSerializer,
    DetailedCodeSessionKeySerializer,
    FollowerSerializer,
    FollowingCreateSerializer,
    FollowingSerializer,
    TokenSerializer,
    TwoFactorAuthenticationCodeSerializer,
    UserCustomSerializer,
    UserDefaultSerializer,
    UserDetailSerializer,
    UserDetailTimezonesSerializer,
)
from users.services import (
    annotate_follows_queryset,
    annotate_users_queryset,
    get_user_login_token,
    make_2fa_authentication,
    remove_user_token,
)
from users.tasks import send_2fa_code_mail_message

User = get_user_model()


@extend_schema_view(
    list=extend_schema(
        request=None,
        parameters=[
            OpenApiParameter(
                name="search",
                description="Search username query. Length must be 3 and more. Required",
                type=str,
                required=True,
            ),
        ],
        responses={
            status.HTTP_200_OK: UserDefaultSerializer,
        },
        description="Endpoint to search users by username.",
    ),
    create=extend_schema(
        request=UserDetailSerializer,
        responses={status.HTTP_201_CREATED: UserDefaultSerializer, status.HTTP_400_BAD_REQUEST: DetailedCodeSerializer},
        description="Endpoint to create new user.",
    ),
    update_me=extend_schema(
        request=UserDetailSerializer,
        responses={
            status.HTTP_204_NO_CONTENT: None,
            status.HTTP_400_BAD_REQUEST: DetailedCodeSerializer,
        },
        description="Endpoint to update your user.",
    ),
    me=extend_schema(
        request=None,
        responses={status.HTTP_200_OK: UserDetailTimezonesSerializer},
        description="Endpoint to get info about you.",
    ),
    login=extend_schema(
        request=AuthTokenSerializer,
        responses={
            status.HTTP_200_OK: TokenSerializer,
            status.HTTP_202_ACCEPTED: DetailedCodeSessionKeySerializer,
            status.HTTP_400_BAD_REQUEST: None,
        },
        description="Endpoint to log in.",
    ),
    logout=extend_schema(
        request=None, responses={status.HTTP_204_NO_CONTENT: None}, description="Endpoint to log out."
    ),
    two_factor_authentication=extend_schema(
        request=TwoFactorAuthenticationCodeSerializer,
        responses={status.HTTP_200_OK: TokenSerializer, status.HTTP_400_BAD_REQUEST: DetailedCodeSerializer},
        description="Endpoint to send 2FA code to log in.",
    ),
)
class UserViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = UserDetailSerializer
    queryset = User.objects.filter()
    permission_classes = (UserPermission,)

    def get_serializer_class(self, *args, **kwargs):
        if self.action == "list":  # noqa
            return UserCustomSerializer
        return self.serializer_class

    def get_queryset(self):
        if self.action == "list":  # noqa
            query = self.request.query_params.get("search", "")
            if len(query) < 3:
                return User.objects.none()
            queryset = User.objects.filter(username__startswith=query, is_private=False)
            return annotate_users_queryset(self.request.user, queryset)

        return self.queryset

    @action(methods=["get"], detail=False, url_name="me", permission_classes=(permissions.IsAuthenticated,))
    def me(self, request: Request) -> Response:
        return Response(
            {"user": self.serializer_class(instance=request.user).data, "availible_timezones": pytz.common_timezones},
            status=status.HTTP_200_OK,
        )

    @action(methods=["post"], detail=False, url_name="login")
    def login(self, request: Request) -> Response:
        serializer = AuthTokenSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        if user.is_2fa_enabled and user.email:
            code = make_2fa_authentication(request.session, user)
            send_2fa_code_mail_message.apply_async(args=[user.email, code], queue="normal_priority")
            request.session.create()

            return Response(
                {
                    "code": "CODE_SENDED",
                    "detail": "2FA Code has been sended to your email.",
                    "session_key": request.session.session_key,
                },
                status=status.HTTP_202_ACCEPTED,
            )

        return Response({"token": get_user_login_token(user), "user_id": user.id}, status=status.HTTP_200_OK)

    @action(methods=["get"], detail=False, url_name="logout", permission_classes=(permissions.IsAuthenticated,))
    def logout(self, request: Request) -> Response:
        remove_user_token(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=["post"], detail=False, url_name="2fa", url_path="two-factor-authentication")
    def two_factor_authentication(self, request: Request) -> Response:
        serializer = TwoFactorAuthenticationCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data["auth_code"]

        session = SessionStore(session_key=serializer.validated_data["session_key"])

        if session.get("2fa_code", 0) == code:
            pk = session["2fa_code_user_id"]
            session.flush()
            session.set_expiry(0)

            return Response(
                {"token": get_user_login_token(get_object_or_404(User, pk=pk)), "user_id": pk},
                status=status.HTTP_200_OK,
            )

        return Response(
            {"detail": "This 2FA code is invalid", "code": "CODE_INVALID"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(methods=["patch", "put"], detail=False, url_path="update-me", url_name="update")
    def update_me(self, request: Request) -> Response:
        serializer = self.serializer_class(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    create=extend_schema(
        request=FollowingCreateSerializer,
        responses={
            status.HTTP_201_CREATED: FollowingCreateSerializer,
            status.HTTP_404_NOT_FOUND: DetailedCodeSerializer,
        },
        description="Endpoint to follow on user.",
    ),
    disfollow=extend_schema(
        request=FollowingCreateSerializer,
        responses={status.HTTP_204_NO_CONTENT: None, status.HTTP_400_BAD_REQUEST: None},
        description="Endpoint to disfollow from user.",
    ),
)
class FollowingsViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = FollowingCreateSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        following = get_object_or_404(User, pk=request.data.get("following", 0))
        if following == request.user:
            return Response({"detail": "User is invalid.", "code": "invalid"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(follower=self.request.user, following=following)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(methods=["post"], detail=False, url_name="disfollow")
    def disfollow(self, request: Request) -> Response:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        following = get_object_or_404(User, pk=request.data.get("following", 0))
        follow = Follow.objects.filter(follower=request.user, following=following)  # noqa

        if follow.exists():
            follow.delete()

            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    list=extend_schema(
        request=None,
        responses={status.HTTP_200_OK: FollowingSerializer, status.HTTP_404_NOT_FOUND: DetailedCodeSerializer},
        parameters=[OpenApiParameter(name="search", description="Search username query", type=str)],
        description="Endpoint to get user followings and search it.",
    )
)
class FollowingsUserAPIView(generics.ListAPIView):
    serializer_class = FollowingSerializer
    lookup_url_kwarg = "pk"

    def get_queryset(self):
        user = get_object_or_404(User, pk=self.kwargs[self.lookup_url_kwarg])
        query = self.request.query_params.get("search", None)
        queryset = user.following if not query else user.following.filter(following__username__startswith=query)
        return annotate_follows_queryset(self.request.user, queryset, "following")


@extend_schema_view(
    list=extend_schema(
        request=None,
        responses={
            status.HTTP_200_OK: FollowerSerializer,
        },
        description="Endpoint to get your followers.",
    )
)
class FollowersViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = FollowerSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        queryset = self.request.user.followers
        return annotate_follows_queryset(self.request.user, queryset, "follower")


class GetUserInfoAPIView(views.APIView):
    @extend_schema(
        request=None,
        responses={
            status.HTTP_200_OK: UserCustomSerializer,
        },
        parameters=[
            OpenApiParameter(name="username", description="Username of user.", type=str, required=True),
            OpenApiParameter(
                name="fields",
                description="Fields in response. Valid values is posts_count, "
                "is_followed, followers_count, followings_count, all.",
                type=str,
                required=True,
            ),
        ],
        description="Endpoint to get info about some user.",
    )
    def get(self, request: Request) -> Response:
        queryset = User.objects.filter()
        fields = request.query_params.get("fields", "")
        queryset = queryset.filter(username=request.query_params.get("username", ""))
        if fields != "all":
            fields = fields.split(",")
        else:
            fields = None

        queryset = annotate_users_queryset(request.user, queryset, fields)
        user = queryset.first()
        serialized_user = UserCustomSerializer(user)

        return Response(serialized_user.data, status=status.HTTP_200_OK)
