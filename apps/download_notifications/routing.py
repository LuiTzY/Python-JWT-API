#Archivo para las rutas websockets de la aplicacion
from django.urls import path
from . import consumers

from .views import ZoomRecordDownloadView


urlpatterns = [
    path('api/download/', ZoomRecordDownloadView.as_view(), name='download'),
]

websocket_urlpatterns = [
    path('ws/download_progress/', consumers.DownloadConsumer.as_asgi()),
    
]

