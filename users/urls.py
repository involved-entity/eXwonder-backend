from django.urls import include, path
from rest_framework import routers

from users.views import UserViewSet

app_name = "api"

router = routers.SimpleRouter()
router.register(r"account", UserViewSet, basename="account")

urlpatterns = [
    path("", include(router.urls))
]
