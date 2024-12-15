from django.urls import path

from notifications.consumers import NotificationConsumer

websocket_urlpatterns = [
    path("messenger/", NotificationConsumer.as_asgi()),
]
