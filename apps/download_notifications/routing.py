#Archivo para las rutas websockets de la aplicacion
from django.urls import path
from . import consumers

from .views import ZoomRecordDownloadView

#Rutas que responden al protocolo HTTP
urlpatterns = [
    path('api/download/', ZoomRecordDownloadView.as_view(), name='download'),
]

#Rutas que corresponden al protoclo Websocket
websocket_urlpatterns = [
    path('ws/download_progress/', consumers.DownloadConsumer.as_asgi()),
    
]

