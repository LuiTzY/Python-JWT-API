import aiohttp
import asyncio
from channels.layers import get_channel_layer

 
 #Va a recibir una tupla de las urls junto con informacion del video incluyendo el save_path
async def start_downloads( urls):
        tasks = [download_video(url[0], url[1], 'download_progress') for url in urls]
        #toma la lista de tareas, y las descarga todas al mismo tiempo de manera asyncronica, *tasks xq es una lista
        await asyncio.gather(*tasks)
    
    #Esta funcion va a descargar cada video, lo que siempre creara una httpp sesion independiente de cada video
async def download_video(url,save_path,channel_name):
        #se crea una sesion http para el cliente
        async with aiohttp.ClientSession() as session:
            #Se llama asincronamente para obtener el video
            async with session.get(url) as response_video:
                #si obtuvimos un estado 200 del servidor de zoom, descargamos el video
                if response_video.status == 200:
                    #dentro de las cabeceras obtenemos lo que pesa el archivo en bytes y lo convertimos a un entero ya que por defecto es un string
                    total_size = int(response_video.headers.get('content-length', 0))
                    downloaded = 0
                    #Descargamos el video en la ruta de guardado y abrimos como binario 
                    with open(save_path, 'ab') as f:
                        async for chunk in response_video.content.iter_any():
                            f.write(chunk)
                            downloaded += len(chunk)
                            print(f"Este es largo del chunk en la descarga {downloaded}")

                            progress = (downloaded) * 100
                            #enviamos el progreso de descarga al frontend
                            #Esta es la informacion que enviamos al cliente, enviaremos el progreso de descarga de cada video
                            await send_progress({'url': url, 'progress': progress,'video':save_path})
                            
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
async def start_downloads( urls):
        tasks = [download_video(url[0], url[1], 'download_progress') for url in urls]
        await asyncio.gather(*tasks)
        
def start_downloads_sync(urls):
    
    print(f"Estas osn las urls {urls}")
    asyncio.run(start_downloads(urls))
