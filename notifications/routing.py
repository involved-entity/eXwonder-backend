from django.urls import path

from notifications.consumers import NotificationConsumer

websocket_urlpatterns = [
    path("", NotificationConsumer.as_asgi()),
]
