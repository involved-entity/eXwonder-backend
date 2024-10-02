from rest_framework.routers import SimpleRouter
from posts.views import PostViewSet
from django.urls import path, include

app_name = "posts"

router = SimpleRouter()
router.register(r"posts", PostViewSet, basename="posts")

urlpatterns = [
    path("", include(router.urls))
]
