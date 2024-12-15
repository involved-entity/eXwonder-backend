import os

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

from messenger.routing import websocket_urlpatterns as message_urls
from notifications.routing import websocket_urlpatterns as notifications_urls

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": URLRouter(notifications_urls + message_urls),
    }
)
