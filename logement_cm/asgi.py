"""
ASGI config for logement_cm project.

HTTP est servi par Django, les WebSockets (notifications instantanées) par Channels.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logement_cm.settings')
django_asgi_app = get_asgi_application()  # doit précéder les imports qui touchent aux modèles

from channels.auth import AuthMiddlewareStack  # noqa: E402
from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402
from channels.security.websocket import AllowedHostsOriginValidator  # noqa: E402

import notifs.routing  # noqa: E402

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AllowedHostsOriginValidator(
        AuthMiddlewareStack(URLRouter(notifs.routing.websocket_urlpatterns))
    ),
})
