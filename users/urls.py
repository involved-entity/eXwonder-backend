from dj_rest_auth.views import PasswordChangeView, PasswordResetConfirmView, PasswordResetView
from django.urls import include, path
from rest_framework import routers

from users.views import FollowsViewSet, UserViewSet

app_name = "api"

router = routers.SimpleRouter()
router.register(r"account", UserViewSet, basename="account")
router.register(r"follows", FollowsViewSet, basename="follows")

urlpatterns = [
    path("", include(router.urls)),
    path("password-change/", PasswordChangeView.as_view(), name="password-change"),
    path("password-reset/", PasswordResetView.as_view(), name="password-reset"),
    path("password-reset-confirm/", PasswordResetConfirmView.as_view(), name="password-reset-confirm")
]

"""
api/v1/follows/ | get | list of my followings
api/v1/follows/{id}/ | get | list of id followings
api/v1/follows/ | post | add new following
api/v1/follows/ | delete | delete following
"""
