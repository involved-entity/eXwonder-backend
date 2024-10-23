from django.urls import include, path
from rest_framework.routers import SimpleRouter

from posts.views import CommentViewSet, PostLikeViewSet, PostViewSet, SavedViewSet

app_name = "posts"

router = SimpleRouter()
router.register(r"posts", PostViewSet, basename="posts")
router.register(r"post-likes", PostLikeViewSet, basename="likes")
router.register(r"comments", CommentViewSet, basename="comments")
router.register(f"saved", SavedViewSet, basename="saved")

urlpatterns = [
    path("", include(router.urls))
]
