import os
import httpx
import asyncio
from channels.layers import get_channel_layer
from apps.drive.services import DriveService



 #Va a recibir una tupla de las urls junto con informacion del video incluyendo el save_path
async def start_downloads(clients,mentor_credentials):
        tasks = [download_video(client, 'download_progress',mentor_credentials) for client in clients]

        #toma la lista de tareas, y las descarga todas al mismo tiempo de manera asyncronica, *tasks xq es una lista
        await asyncio.gather(*tasks)
    
    #Esta funcion va a descargar cada video, lo que siempre creara una httpp sesion independiente de cada video para descargar e enviar la informacion individual de esa grabacion
async def download_video(data,channel_name,mentor_credentials):
        
        #url de descarga de la grabacion
        download_url = f"{data['client_record_details'][0]['download_url']}"
        print(download_url)
        #headers que se enviara para la descarga de una grabacion, xq puede que tengan un play_pass_code y enviando el token en las cabeceras permite acceder a ella
        headers = {
            "Authorization":f"Bearer {mentor_credentials.access_token}",
            
        }
      
        
        "No se esta teniendo en cuenta si el token del mentor se invalida en una solicitud de estas"
        
        #se crea una instancia de un cliente asyncrono de httpx, admite redireccionamiento ya que zoom al descargar una reunion va a redireccionar al servidor donde apunta la grabacion
        async_client = httpx.AsyncClient(headers=headers,follow_redirects=True)
        
        #hacemos la solicitud asyncronamente con la instancia del cliente, asi siempre creara una instancia nueva para cada cliente que haya que descargar una grabacion
        async with async_client.stream('GET', url=download_url,) as response:
             
            print(f"Codigo de estado que obtenemos al intentar descargar {response.status_code} \n")
            if response.status_code == 200:
                print("OBTUVIMOS UN 200 empezara la descarga asincrona")
                #total en bytes de lo que pesa la grabacion
                total_size = data['client_record_details'][0]['file_size']
                downloaded = 0

                
                #creamos la carpeta en el disco duro para ese cliente si es que no existe
                if not os.path.exists(data['client_folder_details']['folder_record_client']):
                        os.makedirs(data['client_folder_details']['folder_record_client'])  
                                        
                # #Descargamos el video en la ruta de guardado y abrimos como permisos de binario (ab)
                
                with open(data['client_folder_details']['folder_record_name'], 'wb') as f:
                    async for chunk in response.aiter_bytes():
                        f.write(chunk)
                        #Calculamos el porcentaje de descargar obtenido
                        downloaded += len(chunk)
                        print(f"Empezo la descarga del video {data['client_record_details'][0]['download_url']} \n")

                        progress = (downloaded / total_size ) * 100 # dividir total_sixe con downloaded para obtener el progreso total correctamente multiplicado x 100
                        #enviamos el progreso de descarga al frontend
                        #Esta es la informacion que enviamos al cliente, enviaremos el progreso de descarga de cada video
                        
                        
                        
                        await send_progress({
                            'client_name': data['client_info']['nombre'],
                            'client_email':data['client_info']['email'],
                            'url': data['client_record_details'][0]['download_url'],
                            'progress': progress,'video':data['client_folder_details']['folder_record_name']
                            })
                        print(f"Credenciales o instancia directamente del mentor {mentor_credentials}")
                        #Aqui deberia de ir la creacion de la carpeta del drive de ese cliente perced para ese mentor directamente
                       
                        #Hacemos otra solicitud para subir el video
                        # asyncio.run(drive_service.post_drive_req)                        
            #Si ocurrio un error al hacer la solicitud enviamos un mensaje de que no se pudo descargar junto con la grabacion que pertenece al cliente
            else:
                await send_progress({"client_name":data['client_info']['nombre'],"error":"Ocurrio esto y no se pudo descargar la grabacion"})

            

      
        

#Funcion que envia el progreso de las descargas a los consumidores del websocket              
async def send_progress(message):
        
        #obtenemos la lista de canales de websockets
        chanel_layer = get_channel_layer()

        #dentro e la lista de canales de los websockets, le enviaremos la informacion al download_progress
        await chanel_layer.group_send(
            'download_progress',
            {
                'type': 'send_progress_message',#nombre del metodo de mi consumidor que va a tomar este mensaje
                'message': message #Mensaje que se le enviara
            }
        )
        
        #al final cuando hacemos esto es como si llamaramos la funcion de nuestro consumidor
        #download_progress y le pasamos el mensaje como parametro, que es el que espera

#va a iniciar una lista siendo cada indice una tarea para descargar cada grabacion de manera sincronica, nada sera interrumpido
def start_downloads_sync(clients,mentor_credentials):
    
    asyncio.run(start_downloads(clients,mentor_credentials))
