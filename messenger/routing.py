from django.urls import path

from messenger.consumers import MessengerConsumer

websocket_urlpatterns = [
    path("messenger/", MessengerConsumer.as_asgi()),
]
