from django.urls import include, path
from rest_framework.routers import SimpleRouter

from posts.views import CommentLikeViewSet, CommentViewSet, PinPostsViewSet, PostLikeViewSet, PostViewSet, SavedViewSet

app_name = "posts"

router = SimpleRouter()
router.register(r"posts", PostViewSet, basename="posts")
router.register(r"post-likes", PostLikeViewSet, basename="likes")
router.register(r"comment-likes", CommentLikeViewSet, basename="comment-likes")
router.register(r"comments", CommentViewSet, basename="comments")
router.register("saved", SavedViewSet, basename="saved")
router.register(r"pinned", PinPostsViewSet, basename="pinned")

urlpatterns = [
    path("", include(router.urls)),
]
