from django.urls import include, path
from rest_framework import routers

from users.views import CustomAuthTokenLoginAPIView, UserViewSet

app_name = "api"

router = routers.SimpleRouter()
router.register(r"account", UserViewSet, basename="account")

urlpatterns = [
    path("", include(router.urls)),
    path("login/", CustomAuthTokenLoginAPIView.as_view(), name="login")
]
