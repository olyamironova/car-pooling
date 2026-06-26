# asgi.py
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.conf import settings
from django.contrib.staticfiles.handlers import ASGIStaticFilesHandler
import rides.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'carpool.settings')

application = ProtocolTypeRouter({
    'http': ASGIStaticFilesHandler(get_asgi_application()),
    'websocket': AuthMiddlewareStack(
        URLRouter(
            rides.routing.websocket_urlpatterns
        )
    ),
})