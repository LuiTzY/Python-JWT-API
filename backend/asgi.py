import os
from channels.routing import ProtocolTypeRouter,URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
from apps.download_notifications.routing import websocket_urlpatterns
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

#ProtocolTypeRouter me permite dirigir la solicitud segun el tipo que sea, http y webscoket en estos casos
application = ProtocolTypeRouter({
    "http":get_asgi_application(),
    #AuthMiddleware autentica todas las rutas por websockets
    "websocket":AuthMiddlewareStack(
        #Mapea las urls de los websockets a sus respectivos consumidores(que es como si fuesen vistas normales por asi decirlo)
        URLRouter(
            websocket_urlpatterns
        )
    )
})