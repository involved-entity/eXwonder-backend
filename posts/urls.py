from django.urls import include, path
from rest_framework.routers import SimpleRouter

from posts.views import LikeViewSet, PostViewSet, CommentViewSet

app_name = "posts"

router = SimpleRouter()
router.register(r"posts", PostViewSet, basename="posts")
router.register(r"likes", LikeViewSet, basename="likes")
router.register(r"comments", CommentViewSet, basename="comments")

urlpatterns = [
    path("", include(router.urls))
]
