from django.contrib.auth import get_user_model
from rest_framework import mixins, viewsets

from users.permissions import UserPermission
from users.serializers import UserSerializer

User = get_user_model()


class UserViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = UserSerializer
    queryset = User.objects.filter()
    permission_classes = UserPermission,
