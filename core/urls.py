from django.urls import include, path

urlpatterns = [
    path("api/v1/users/", include("users.urls")),
    path("api/v1/posts/", include("posts.urls")),
]
