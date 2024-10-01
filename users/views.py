from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from users.permissions import UserPermission
from users.serializers import (
    DetailedCodeSerializer,
    TokenSerializer,
    TwoFactorAuthenticationCodeSerializer,
    UserSerializer,
)
from users.services import get_user_login_token, make_2fa_authentication
from users.tasks import send_2fa_code_mail_message

User = get_user_model()


@extend_schema_view(
    create=extend_schema(request=UserSerializer),
    update=extend_schema(request=UserSerializer),
    retrieve=extend_schema(request=None, responses={
        status.HTTP_200_OK: UserSerializer
    })
)
class UserViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = UserSerializer
    queryset = User.objects.filter()
    permission_classes = UserPermission,

    @extend_schema(request=AuthTokenSerializer, responses={
        status.HTTP_200_OK: TokenSerializer,
        status.HTTP_202_ACCEPTED: DetailedCodeSerializer,
        status.HTTP_400_BAD_REQUEST: None
    })
    @action(methods=["post"], detail=False, url_name="login")
    def login(self, request: Request) -> Response:
        serializer = AuthTokenSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        if user.is_2fa_enabled and user.email:
            code = make_2fa_authentication(request.session, request.user)
            send_2fa_code_mail_message.delay(request.user.email, code)

            return Response({
                "code": "CODE_SENDED",
                "detail": "2FA Code has been sended to your email."
            }, status=status.HTTP_202_ACCEPTED)

        return Response({
            "token": get_user_login_token(user)
        }, status=status.HTTP_200_OK)

    @extend_schema(request=TwoFactorAuthenticationCodeSerializer, responses={
        status.HTTP_200_OK: TokenSerializer,
        status.HTTP_400_BAD_REQUEST: DetailedCodeSerializer
    })
    @action(methods=["post"], detail=False, url_name="2fa")
    def two_factor_authentication(self, request: Request) -> Response:
        serializer = TwoFactorAuthenticationCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data["auth_code"]

        if request.session.get("2fa_code", 0) == code:
            pk = request.session["2fa_code_user_id"]
            request.session.flush()
            request.session.set_expiry(0)

            return Response({
                "token": get_user_login_token(get_object_or_404(User, pk=pk))
            }, status=status.HTTP_200_OK)

        return Response({
            "detail": "This 2FA code is invalid. May be it has been expired, so regenerate a code.",
            "code": "CODE_INVALID"
        }, status=status.HTTP_400_BAD_REQUEST)
