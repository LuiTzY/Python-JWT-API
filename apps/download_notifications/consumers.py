import json
from channels.generic.websocket import AsyncWebsocketConsumer

"""
    Este archivo es igual que una vista tradicional de django http, pero esta es manejada por websockets en estos casos
"""


class DownloadConsumer(AsyncWebsocketConsumer):
    async def connect(self):
            self.group_name = 'download_progress'
            await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
            )
            
            await self.accept()
            
            await self.send(text_data=json.dumps({
             "conection_status":"Conexion Establecida",
            
         }))
           
            

    async def receive(self, text_data):
        pass

    
    async def disconnect(self, close_code):
        print(f"CODIGO DE DESCONEXION {close_code}")
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
    
    #Envia mensaje de progreso de la descarga al frontend
    async def send_progress_message(self,event):
         # Recibir el mensaje de progreso de descarga
        progress_message = event['message']

        # Enviar el progreso de descarga al cliente
        await self.send(text_data=json.dumps({
            'progress': progress_message
        }))