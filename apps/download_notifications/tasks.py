import aiohttp
import asyncio
from channels.layers import get_channel_layer
import os
from yarl import URL

#Las corutinas son funciones que trabajan asincronamente, tareas que duren mas que otras sera ejecutadas primeros, nunca va a esperar a que la tarea anterior termine 

 #Va a recibir una tupla de las urls junto con informacion del video incluyendo el save_path
async def start_downloads(clients,mentor_credentials):
        print(clients)
        tasks = [download_video(client, 'download_progress',mentor_credentials) for client in clients]
        #toma la lista de tareas, y las descarga todas al mismo tiempo de manera asyncronica, *tasks xq es una lista
        await asyncio.gather(*tasks)
    
    #Esta funcion va a descargar cada video, lo que siempre creara una httpp sesion independiente de cada video
async def download_video(data,channel_name,mentor_credentials):
        headers = {
            "Authorization":mentor_credentials
        }
        url = URL(data['client_record_details'][0]['download_url'], encoded=True)

        print(headers)
        #se crea una sesion http para el cliente
        async with aiohttp.ClientSession() as session:
            #Se llama asincronamente para obtener el video
            async with session.get(url=data['client_record_details'][0]['download_url'],  headers=headers) as response_video:
                print("Cabeceras de la solicitud:")
                
                for key, value in headers.items():
                    print(f"{key}: {value}\n")               
                
                
                print(f" Url {response_video.url} \n")
                print(await response_video.text())
                if response_video.status == 200:
                    #dentro de las cabeceras obtenemos lo que pesa el archivo en bytes y lo convertimos a un entero ya que por defecto es un string
                    total_size = data['client_record_details']['size']
                    downloaded = 0
                    
                    #creamos la carpeta en el disco duro para ese cliente si es que no existe
                    if not os.path.exists(data['client_folder_details']['folder_record_client']):
                           os.makedirs(data['client_folder_details']['folder_record_client'])  
                                             
                    #Descargamos el video en la ruta de guardado y abrimos como permisos de binario (ab)
                    with open(data['client_folder_details']['folder_record_name'], 'wb') as f:
                        async for chunk in response_video.content.iter_any():
                            f.write(chunk)
                            downloaded += len(chunk)
                            print(f"Este es largo del chunk en la descarga {downloaded}")

                            progress = (downloaded / total_size ) * 100 # dividir total_sixe con downloaded para obtener el progreso total correctamente multiplicado x 100
                            #enviamos el progreso de descarga al frontend
                            #Esta es la informacion que enviamos al cliente, enviaremos el progreso de descarga de cada video
                            await send_progress({
                                'client_name': data['client_info']['nombre'],
                                'client_email':data['client_info']['email'],
                                'url': data['client_record_details']['download_url'],
                                'progress': progress,'video':data['client_folder_details']['folder_record_name']
                                })
                
                else:
                    
                    print(f"No se puede descargar DEBIDO A ESTO {response_video.content}\n")
                    print(f"No se puede descargar DEBIDO A ESTO {response_video.text} {response_video.status}\n")


#Funcion que envia el progreso de las descargas a los consumidores del websocket              
async def send_progress( message):
        chanel_layer = get_channel_layer()
     
        print(f"Este es el chanell layer actual por el cual se esta enviando el progreso de descarga de los videos {chanel_layer} \n")
        await chanel_layer.group_send(
            'download_progress',
            {
                'type': 'send_progress_update',
                'message': message
            }
        )
        

        
def start_downloads_sync(clients,mentor_credentials):
    
    print(f"Estas osn los clientes {clients}")
    asyncio.run(start_downloads(clients,mentor_credentials))
