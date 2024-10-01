from dj_rest_auth.views import PasswordChangeView, PasswordResetConfirmView, PasswordResetView
from django.urls import include, path
from rest_framework import routers

from users.views import CustomAuthTokenLoginAPIView, UserViewSet

app_name = "api"

router = routers.SimpleRouter()
router.register(r"account", UserViewSet, basename="account")

# ACTIONS IN VIEWSET !!

urlpatterns = [
    path("", include(router.urls)),
    path("login/", CustomAuthTokenLoginAPIView.as_view(), name="login"),
    path("password-change/", PasswordChangeView.as_view(), name="password-change"),
    path("password-reset/", PasswordResetView.as_view(), name="password-reset"),
    path("password-reset-confirm/", PasswordResetConfirmView.as_view(), name="password-reset-confirm")
]
