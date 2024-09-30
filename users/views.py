import pytz
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.request import Request
from rest_framework.response import Response

from users.permissions import UserPermission
from users.serializers import TokenSerializer, UserSerializer

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


class CustomAuthTokenLoginAPIView(ObtainAuthToken):
    @extend_schema(request=AuthTokenSerializer, responses={
        status.HTTP_200_OK: TokenSerializer
    })
    def post(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, _ = Token.objects.get_or_create(user=user)   # noqa
        utc = timezone.now().replace(tzinfo=pytz.utc)

        if token.created > utc - (60 * 60 * settings.TOKEN_EXP_TIME):
            token.delete()
            token = Token.objects.create(user=user)   # noqa

        return Response({
            "token": token.key
        }, status=status.HTTP_200_OK)
