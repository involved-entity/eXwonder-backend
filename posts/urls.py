from django.urls import include, path
from rest_framework.routers import SimpleRouter

from posts.views import LikeViewSet, PostViewSet

app_name = "posts"

router = SimpleRouter()
router.register(r"posts", PostViewSet, basename="posts")
router.register("likes", LikeViewSet, basename="likes")

urlpatterns = [
    path("", include(router.urls))
]
