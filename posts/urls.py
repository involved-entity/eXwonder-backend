from django.urls import include, path
from rest_framework.routers import SimpleRouter

from posts.views import CommentViewSet, PostLikeViewSet, PostViewSet

app_name = "posts"

router = SimpleRouter()
router.register(r"posts", PostViewSet, basename="posts")
router.register(r"post-likes", PostLikeViewSet, basename="likes")
router.register(r"comments", CommentViewSet, basename="comments")

urlpatterns = [
    path("", include(router.urls))
]
