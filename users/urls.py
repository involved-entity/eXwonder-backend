from dj_rest_auth.views import PasswordChangeView, PasswordResetConfirmView, PasswordResetView
from django.urls import include, path
from rest_framework import routers

from users.views import FollowersViewSet, FollowingsUserAPIView, FollowingsViewSet, UserViewSet

app_name = "users"

router = routers.SimpleRouter()
router.register(r"account", UserViewSet, basename="account")
router.register(r"followings", FollowingsViewSet, basename="followings")
router.register(r"followers", FollowersViewSet, basename="followers")

urlpatterns = [
    path("", include(router.urls)),
    path("followings/user/<int:pk>/", FollowingsUserAPIView.as_view(), name="followings-user"),
    path("password-change/", PasswordChangeView.as_view(), name="password-change"),
    path("password-reset/", PasswordResetView.as_view(), name="password-reset"),
    path("password-reset-confirm/", PasswordResetConfirmView.as_view(), name="password-reset-confirm")
]
