import os
import json
import base64
import datetime
import requests
from .models import Zoom
from dotenv import load_dotenv
from errors.models import ZoomRecordingError
from calendly.services import CalendlyService
load_dotenv()

class ZoomService():
    def __init__(self):
        #instancio la clase y automaticamente se inicia la conexion a la base de datos
        self.zoom_token_url = 'https://zoom.us/oauth/token/'
        self.zoom_refresh_token_url = 'https://zoom.us/oauth/token/'
        self.clientID = os.getenv("clientID")
        self.clientSecret = os.getenv("clientSecret")
        self.redirectURL = os.getenv("redirectURL")
        self.storage_url = "D:/Zoom Grabaciones/"
        self.calendly = CalendlyService()
        self.clients = self.calendly.get_scheduled_events_invite_email()
        
    #se le debe de pasar el codigo de autorizacion para la solicitud 
    def zoom_token_auth_params (self, code):
       #esta funcion devuelve los parametros que van en el header de la solicitud que se le hara a la api de zoom, son necesarioas ya que zoom utiliza el estandar Oauth 2.0
       #para obtener un token de acceso
        return {
            'grant_type': 'authorization_code',  
            'code': code, #codigo de autorizacion
            'redirect_uri': self.redirectURL,
            'client_id': self.clientID,       
            'client_secret':self.clientSecret  
        }
        
    #Este metodo se va a ejecutar cuando haya un post en el api view de zoom
    def get_access_token(self,auth_code):
        try:
        # Hacemos una solicitud POST a la url para obtener el token de acceso, refresh token y otras opciones como el scope etc
            response = requests.post(
                                url=self.zoom_token_url, # url a la que se le hace solicitud una vez obtenido un codigo de autorizacion para obtener un token de acceso
                                headers=self.get_authorization_header(), #se obtiene las cabeceras necesarias para que zoom valide la peticion
                                params=self.zoom_token_auth_params(auth_code) #parametros requerido para la peticion para obtener el access token
                                ) 
            #si ocurrio un error con la solicitud, lanzara un error para que la excepcion lo capture
            response.raise_for_status()
            
        except requests.exceptions.HTTPError as e:
            print("Ocurrio un Error de autorizacion codigo invalido \n")
            #e es el error que ha ocurrido, y 1 significa que la solicitud se proceso pero hubo un error con el codigo de autorizacion de zoom para la app (es invalido)
            return [0,e]
        else:
            credentials = response.json()
            #si las credenciales se guardaron correctamente en la base de datos una vez hecha la autorizacion, devolvemos una lista con un 0
            #indicando que no ocurrieron errores y las credenciales se guardaron
         
            #si la respuesta fallo devolvemos un 1 de que esta fue fallida, e imprimimos el error
            return [1,credentials]
    
    #metodo para unir el clientID y clientSecret, encondeados en base 64
    def encode_app_credentials(self):
        #se encodean en base 64, el client secret de la app y el client id, para formar uno solo
        #esto es debido a que zoom lo requiere para la  hora de hacer la solicitud por post
        #ya que los datos son sensibles y deben estar en un formato seguro para luego ser examinados correctamente
        auth =  f"{self.clientID}:{self.clientSecret}"
        auth_encode = auth.encode("ascii")
        auth_b64 = base64.b64encode(auth_encode)
        auth_value = auth_b64.decode("ascii")
        #retorna el valor 
        return auth_value

    def get_authorization_header(self):
        #headers necesarios para obtener un token de acceso luego de que la app haya sido autorizada
        return {
        #host
        "Host": "zoom.us",
        #Authorization, lleva la estructura de Basic + los tokens codificados en base a 64 bits, zoom lo requiere asi para su peticion
        "Authorization": f"Basic {self.encode_app_credentials()}",
        #el tipo de dato que espera la api de zoom para la solicitud
        "Content-Type": "application/x-www-form-urlencoded",
        }
        
    def refresh_token(self,user_id):
        #Se hace una consulta para obtener las credenciales
        tokens = Zoom.objects.get(user__id = user_id)
        try:
            #Hacemos una solicitud para refrescar el token, con los parametros necesarios
            token_refreshed = requests.post(url=self.zoom_refresh_token_url,
                      headers=self.zoom_refresh_token_params(),
                      params={
                          'grant_type':'refresh_token',
                          'refresh_token':tokens[1]
                      })
            
            #Invocamos un error si realmente este ocurre con la solicitud
            token_refreshed.raise_for_status()
            
        except  requests.exceptions.HTTPError as e:
            error = str(e)
            #imprimer el error por consola
            print("Error: No se pudo actualizar el token de accesso debido a: {}\n".format(e))
            #retornamos el error junto a un numero 2, que identifca que ocurrio un error con la solicitud
            return [2,e]
        
        else:
            #si entra aqui es porque la respuesta tuvo un estado .ok basicamente un estado (200)
            #se envia las credenciales  actualizado con las demas informaciones
            new_credentials = token_refreshed.json()
            try:
                
            #Actualizamos los tokens de la instancia del usuario al que pertenece
                tokens.access_token = new_credentials['access_token']
                tokens.refresh_token = new_credentials['refresh_token']
                tokens.save()
                print(f"Se guardaron las credenciales\n")
            except Exception as e:
                #retornamos un error ocurrido al intentar guardar en las bd
                return [4,e]
            return [1,new_credentials]

        
    def zoom_refresh_token_params (self):
      return {
          "Host":"zoom.us",
        #Authorization, lleva la estructura de Basic + los tokens codificados en base a 64 bits, zoom lo requiere asi para su peticion
        "Authorization": f"Basic {self.encode_app_credentials()}",
        #el tipo de dato que espera la api de zoom para la solicitud
        "Content-Type": "application/x-www-form-urlencoded",
        }
    
    def zoom_api_get_requests(self,endpoint):
        try:
            #hacemos una solicitud por get al endpoint que nos pasen, y obtenemos los params de las cabeceras
            response = requests.get(url=endpoint,headers=self.get_header_access_token_params())
            print(f"Este es el token con el que se haran las solicitudes {self.get_header_access_token_params()} \n")
            #print(f"Esto son los datos con los que se hara la solicitud {endpoint} cabeceras de la solicitud {self.header_access_token_params}")
            response.raise_for_status()
            
        except requests.exceptions.HTTPError as e:
            
            r = response.json()
            print(f"OCURRIO UN ERROR {r} \n ")

            #verificamos si el token se expiro
            if response.status_code == 401 and r['message'] == "Invalid access token.":
                print("El token es invalido, proporcionara un token correcto \n")
                
                return "El token es invalido, proporcionara un token correcto"
            
            elif response.status_code == 401 and r['message'] == "Access token is expired.":
                print(f"El token expiro, pero se intentara actualizarlo {e} \n")
                
                refresh_token  = self.refresh_token()
                """
                    una vez se intente refrescar el token de refresco podemos obtener 3 tipos de resupuestas indentificados con estos nuemeros
                    #0 No se pudo refrescar el token 
                    #1 Se refresco el token correctamente
                    #2 Ocurrio un error desde el servidor
                    
                    
                    Luego para el manejo de respuestas y errores, seran identificados con estos numeros, estas seran devueltas con el fin de que la funcion
                    que utilice este metodo, espere estos valores para validar el proceso y seguir un mejor flujo:

                    #0 Ocurrio un error con el servidor para refrescar el token
                    #1 El token se actualizo, por lo que ya se podran realizar solicitudes 
                    #2 Ocurrio un error con el servidor de manera interna, por lo que el token no se refresco
                    
                """
                
                #Estas son las respuestas que obtenemos al refrescar el token y es aqui donde enviaremos cada numero identificado por lo dicho anterirormente
                #Los valores retornados sera de una largo de 2, esto es debido a evitar errore de fuera de rango, ya que cuando ocurra un error, se devolvera su numero
                #pero tambien el error, lo cual es correcto, pero cuando sea que se inserto correctamente deberemos de enviar esta misma respuesta
                if refresh_token[0] == 2:                    
                    #retornamos el error que se encuentra en el indice 1, y devolvemos otro 0 indentificado el error
                    return [0,refresh_token[1]]
                
                elif refresh_token[0] == 1:
                    
                    #Si entra aqui, las credenciales fueron actualizadas en la base de datos
                    print("La solicitud se proceso, pero ocurrio un error al guardar las credencianles \n")
                    return [2,2]
                
                #Obtenemos un 0 como respuesta lo que indica que fue exitosa la renovacion del token
                elif refresh_token[0] == 4:
                    print("La solicitud se proceso con exito y las credenciales no se pudieron actualizar correctamente \n")
                    return [1,1]
                
            return f"Ocurrio un error con la solicitud debido a, el token expiro, se hara una solicitud para renovarlo: {e}"
        
        else:
            res = response.json()
            print(f"{res}\n")
            
            return [3,res]
            
            
    def get_storage(self):
        """
             La funcion devolvera 3 numeros, identificados por cada error correspondiente
             #0 La ruta existe, por lo que se podran guardar las grabaciones
             #1 La ruta no se encontro, puede ser debido a que no este conectado el disco duro
             #2 Ocurrio un error inesperado
        """
        try:
            if os.path.exists(self.storage_url):
                print("El directorio esta disponible para guardar las grabaciones de los clientes. \n")
                return True
        except FileNotFoundError:
            error = ZoomRecordingError.objects.create(error="FileNotFoundError")
            
            print("El directorio no se encuentra debido a que el disco duro externo no está conectado. \n ")
            return False
        
        except Exception as e:
            error = str(e)
            er = ZoomRecordingError.objects.create(error=error)
            print(f"Ocurrio un error inesperado \n")
            
            return False
        
    def download_zoom_recordings(self,start_date,end_date):
        
        # Fecha de inicio y fin del rango
        fecha_inicio_str = start_date

        # Convertir las cadenas de fecha en objetos datetime
        fecha_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d")
        
        #la fecha de finalizacion siempre sera la actual
        fecha_fin = datetime.now()
        print("Fecha final {}\n".format(fecha_fin))
  
        
        """
            Bucle para obtener todas las grabaciones, desde la fecha inicial (dada) hasta la fecha actual
            Se hara solicitudes para obtener las grabaciones alojadas en zoom dada una fecha inicial, hara una solicitud
            mes por mes desde la fecha inicial, tendra 2 flujos dependiendo de las respuestas que de la api de zoom
            
            1 Hay una sola grabaciones, se accede al objeto de la grabacion
            2 Hay mas de una grabacione: En este caso se va a iterar por cada objeto que contenga la grabacion
            
            En cada uno de estos el proceso siempre sera el mismo, se hara una solicitud a la api de calendly para obtener los eventos,
            ya que con estos tenemos informacion del id de la reunion de zoom que se haya dado, cuando esto sucede ya la grabacion debera de estar subida
            en la nube de zoom, por lo que esta debera de coincidir con alguno de los clientes asociados a ese id de reunion de zoom de la grabacion
            
            Con esto asociamos un cliente con una grabacion, una vez esto es obtenido se creara un registro de ese cliente, con su nombre y su correo electronico que haya puesto en calendly,
            una vez suceda esto se descargara la grabacion en el disco duro en la ruta indicada, con el nombre de carpeta de la fecha de ese grabacion en si, luego se hace una solicitud para
            enviar al draft esa grabacion de zoom una vez es decargada correctamente (aqui hay que validar ciertos casos: Se descargue correctamente, no se descargue correctamente, no encuentre
            la ruta es decir el (disco duro, que la excepcion seria FileNotFoundError), cualquier caso que ocurra debe de ser guardado en la base de datos, en los casos en que ocurran
            errores el flujo del programa se debe de detener y no seguir
            
        """
        
        #Iteramos hasta que la fecha de inicio sea igual que la fecha actual
        while fecha_inicio <= fecha_fin:
                   
            print("Obteniendo las grabaciones de la fecha: {} \n".format(fecha_inicio.strftime("%Y-%m-%d")))
            # se hace una solicitud a la api de zoom con la fecha que se este iterando con el formato de YYYY-MM--DD, junto con la informacion de los headers
            #response = requests.get(url="https://api.zoom.us/v2/users/me/recordings?from={}&to={}".format(fecha_inicio.strftime("%Y-%m-%d"),fecha_inicio.strftime("%Y-%m-%d")),headers=self.get_header_access_token_params())
            
            response_json = self.zoom_api_get_requests("https://api.zoom.us/v2/users/me/recordings?from={}&to={}".format(fecha_inicio.strftime("%Y-%m-%d"),fecha_inicio.strftime("%Y-%m-%d")))
            #se convierten los datos en formato json de la respuesta de la api de zoom, para poder acceder a ellos y manejarlos           
                
            print("Se obtuvieron esta cantidad de grabaciones de la fecha: {} grabaciones encontradas: {}\n".format(fecha_inicio.strftime("%Y-%m-%d"),response_json[0]['total_records']))
            
            
            #Se consulta el status del disco duro, para ver si esta conectado en la computadora o no, para verificar si las grabaciones pueden ser guardadas
            storage_status = self.get_storage()
            
            #Verificamos la disponibilidad del disco duro
            if not storage_status:
                
                return "El disco duro para guardar las grabaciones no se encuentra conectado en la computadora\n"
            
            #El disco duro esta disponible para almacenar las carpetas
            print("El disco duro se encuentra para descargar las grabaciones \n")   
              
            
            if response_json[1] == 3: #Si obtenemos un 3 de la respuesta, es que se proceso correctamente la solicitud
                
                #accedemos a la respuesta al total de grabaciones, para determinar que funcion sera utilizada para descargar las grabaciones
                #Si solo hay una reunion, se utilizara el metodo para descargarla 
                if response_json[0]['total_records'] == 1:
                #La solicitud fue exitosa por lo que se podran obtener las grabaciones
                    self.download_one_recording(response_json[0]) #pasamos el 0 ya que ahi es que se encuentra los datos de la solicitud de zoom
                        
                elif response_json[0]['total_records'] > 1:
                    #Si hay mas de una reunion entrara aqui
                    self.download_more_videos()
                else:
                    print("No se encontraron grabaciones")
                    return "No se encontraron grabaciones"
                
            else:
                #caso contrario de que no obtengamos un 3, es posible que haya sido un error, por lo que mostraremos simplemente el error que obtuvimos retornandolo
                return response_json
                        
           
        

            
                #se adelanta un año si es diciembre
            if fecha_inicio.month == 12:
                fecha_inicio = datetime(fecha_inicio.year + 1, 1, 9)
            #se adelanta un mes
            else:
                fecha_inicio = datetime(fecha_inicio.year, fecha_inicio.month + 1, 9)
                
    
    def download_one_recording(self, response_json): #response_json va a ser la respuesta de la api de zoom                          
                
                print("Entra aqui ha descargar \n")
                
               
                #El disco duro esta disponible, por lo que seguira el flujo para crear la carpeta y guardar las grabaciones
                
                #instanceamos la clase de calendly
                #obtenemos los eventos que coinciden con la misma fecha
                
                #verificamos que respuesta obtuvimos de los metodos de calendly para mejorar la captura de errores
                
                if self.clients[0] == 1:
                    #Obtenemos loc clientes y hacemos el proceso de la automatizacion
                    #guardamos la informacion de la clienta que coincida con el id de la reunion relacionado
                    clienta_info = self.get_client_by_meeting_id(self.clients[1],response_json["meetings"][0]['id'])
                    
                    print(f"Informacion de la clienta que conciede con el id {clienta_info} id de la reunion {response_json['meetings'][0]['id'] }")
                    nombre_clienta = clienta_info[0]['nombre']
                    correo_clienta = clienta_info[0]['email']
                    
                    
                    print("Nombre de la clienta: {} Correo de la clienta: {}".format(nombre_clienta[0],correo_clienta))
                    
                    #se creara un folder con el nombre del cliente
                    folder_clienta_name = os.path.join(self.storage_url,nombre_clienta)

                    #se crea la carpeta con el nombre de la clienta si no existe                         
                    if not os.path.exists(folder_clienta_name):
                        os.makedirs(folder_clienta_name)
                        
                    #crear archivo de texto en la carpeta de esa grabacion, acerca de la respuesta que se obtuvo
                    with open(os.path.join(folder_clienta_name,"zoom-response.json"),"w",encoding="utf8") as record_file:
                        #se escribe en formato json los datos que nos devuelve zoom como respuesta de la fecha de esa grabacion que se descargara
                        json.dump(response_json,record_file,indent=4)
                    
                    print(f"Se han escrito correctamente los metadatos de la grabacion \n")
                    
                    #Lista de las lista de archivos de las grabaciones, solo almacenara la que es un video y su extension debe der ser MP4 (es necesario, ya que manualmente se tendria que ver)
                    #cual es el indice que tiene ese archivo MP4, y estos indices pueden variar dependiendo si hay archivos de texto o no etc...
                    recording_shared_screen = [grabacion for grabacion in response_json["meetings"][0]['recording_files'] if grabacion['file_extension'] == "MP4"]
                    
                            
                    #obtenemos la fecha de cuando se inicio la reunion
                    fecha_invalid_format = recording_shared_screen[0]["recording_start"]
                    #la convertimos en un formato valido ya que el tipo de objeto que es la fecha es:"2023-10-02T20:25:55Z"
                    fecha_folder = datetime.strptime(fecha_invalid_format, "%Y-%m-%dT%H:%M:%SZ")
                    
                    #se forma una ruta, para crear una carpeta para esa grabacion en esa ruta, el nombre de la carpeta sera la fecha de la grabacion con un formato DATE Ej(2020-12-12)
                    record_folder = os.path.join(folder_clienta_name,f"{fecha_folder.date()}")
                    
                    #Si no existe esa carpeta se creara
                    if not os.path.exists(record_folder):
                        os.makedirs(record_folder)
                    
                    
                    #una vez creada la carpeta, se descargara el video en la ruta del folder de la clienta con la fecha de la grabacion
                    with open(os.path.join(record_folder,"grabacion.mp4"),"wb") as record:
                        """
                            Las grabaciones de los videos se le pueden haber generado una password, lo que haria que la grabacion se descargase incorrectamente
                            y el flujo siguiera como lo previsto, por lo que para evitar esto, enviamos el token de accesso a la url de descarga para asi poder
                            descargarla correctamente
                        """
                        tokens = self.get_zoom_credentials()
                        #video = self.download_url_video(url=f"{records_types['download_url']}")
                        video = requests.get(url=recording_shared_screen[0]['download_url'],stream=True,headers={
                                    'Authorization':'Bearer {}'.format(tokens[0])
                                })

                        # Guardar el progreso de descarga
                        download_progress = 0

                        # Definir el tamaño del bufer para leer los datos, mientra mas alto mas ram consume
                        buffer_size = 1024
                        try:
                            
                            print(f"En el folder {record_folder} se descargara la grabacion de la url: {recording_shared_screen[0]['download_url']}\n")
                            for data in video.iter_content(chunk_size=buffer_size):
                                record.write(data)
                                
                                # Actualizar el progreso de descarga si hay un tamaño de archivo válido
                                if  recording_shared_screen[0]["file_size"] > 0:
                                    download_progress += len(data)
                                    # Calcular el porcentaje de descarga
                                    percentage_progress  = (download_progress / recording_shared_screen[0]["file_size"]) * 100
                                    # Imprimir el porcentaje de descarga
                                    print(f"Progreso de descarga de la grabacion: {percentage_progress :.2f}%\n")
                                    
                        except Exception as e:
                            error = str(e)
                            load_json_error(error)
                            #Ocurrio un error y no se pudo descargar el video, ya sea por temas de red etc
                            #Habria que guardar el error en la base de datos
                            return f"No se pudo guardar el video ya que ocurrio esto: {e}"
                        
                        else:                   
                            print("Se descargo correctamente el video \n")
                    
                            print("Ahora se va a guardar los datos de la clienta en la base de datos \n")
                            
                            insert_client_db = self.db.create_client(clienta_info[0])
                            
                            #Nota, verificar cuando ya un clienta exista
                            if insert_client_db[0] == 1:
                                #si se inserta correctamente el cliente seguira el flujo
                                
                                print("Se guardo en la base de datos la informacion de la clienta \n")
                                
                                    #intenta eliminar la reunion desde la api de zoom, una vez el archivo es descargado
                            try:
                                    delete_recording = requests.delete(url="https://api.zoom.us/v2/meetings/{}/recordings/?delete=trash".format(response_json["meetings"][0]['id']),headers=self.get_header_access_token_params())
                                    #se elimino correctamente, ahora se procedera a subir el video a drive
                                    video_info = {
                                        'video_file_name':"Grabacion de la reunion de {}.mp4".format(fecha_folder.date()),
                                        'video_src':os.path.join(record_folder,"grabacion.mp4")
                                    }
                                    
                                    client_info_details = {
                                        'email':clienta_info[0]['email'],
                                        'client_folder_name':clienta_info[0]['nombre']
                                    }
                                    upload_zoom_video(video_info,client_info_details)
                                    
                                    delete_recording.raise_for_status()
                                    
                            except requests.exceptions.HTTPError as e:
                                error = str(e)
                                load_json_error(error)
                                    
                                print("No se pudo eliminar la reunion debido a que: {}\n".format(delete_recording.json()))
                                    
                                return "No se pudo eliminar la reunion debido a que: {}\n".format(delete_recording.json())
                            
                                
                            else:
                                print("No se pudo guardar en la base de datos la informacion de la clienta\n")
                                
                else:
                    #Retornamos el error
                    return self.clients[1]
                
               
           
                        
                            
    def download_more_videos(self,response_json):
        
        if self.clients[0] == 1:
                
                banned_recordings_id = []              
            #si son mas de una grabacion las que se encuentren en el rango de esas fechas y los ids de estas no estan en los ids baneados
                for record in range(response_json["total_records"]):
                    
                    if response_json["meetings"][record]['uuid'] not in banned_recordings_id:
                        banned_recordings_id.append(response_json["meetings"][record]['uuid'])
                        
                        #estamos iterando por cada diccionario de una grabacion, por lo que descargaremos esa grabacion que se este iterando
                       

                        clienta_info = self.get_client_by_meeting_id(self.clients[1],response_json["meetings"][record]['id'])
                        
                        print(f"Informacion de la clienta que coincide con el id {clienta_info} id de la reunion {response_json['meetings'][0]['id'] }")
                        
                        nombre_clienta = clienta_info[0]['nombre']
                        correo_clienta = clienta_info[0]['email']                        
                        print("Nombre de la clienta: {} {}".format(nombre_clienta[0],nombre_clienta[1]))
                        
                        
                        #se creara un folder con el nombre del cliente
                        folder_clienta_name = os.path.join(self.storage_url,f"{nombre_clienta[0]} {nombre_clienta[1].replace(':', '')}")

                                #se crea la carpeta con el nombre de la clienta si no existe                         
                        if not os.path.exists(folder_clienta_name):
                            os.makedirs(folder_clienta_name)
                            
                        #crear archivo de texto para la clienta
                        with open(os.path.join(folder_clienta_name,"zoom-response.json"),"w",encoding="utf8") as record_file:
                            #se escribe en formato json los datos que nos devuelve zoom como respuesta de la fecha de esa grabacion que se descargara
                            json.dump(response_json,record_file,indent=4)
                        
                        print(f"Se han escrito correctamente los metadatos de la grabacion \n")
                        
                        print(f"LINKS CON LISTA DE COMPRENSION {recording_shared_screen} \n")
                        
                         #Lista de las lista de archivos de las grabaciones, solo almacenara la que es un video
                        recording_shared_screen = [grabacion for grabacion in response_json["meetings"][record]['recording_files'] if grabacion['file_extension'] == "MP4"]
                        
                        #obtenemos la fecha de cuando se inicio la reunion
                        fecha_invalid_format = recording_shared_screen[0]["recording_start"]
                        #la convertimos en un formato valido ya que el tipo de objeto que es la fecha es:"2023-10-02T20:25:55Z"
                        fecha_folder = datetime.strptime(fecha_invalid_format, "%Y-%m-%dT%H:%M:%SZ")
                        

                        #se creara una carpeta para esa grabacion, el nombre de la carpeta sera la fecha de la grabacion
                        record_folder = os.path.join(folder_clienta_name,f"{fecha_folder.date()}")
                        if not os.path.exists(record_folder):
                            os.makedirs(record_folder)
                        
                        #una vez creada la carpeta, se descargara el video en la ruta del folder de la clienta con la fecha de la grabacion
                        with open(os.path.join(record_folder,"grabacion.mp4"),"wb") as zoom_record:
                            
                            tokens = self.get_zoom_credentials()
                            #video = self.download_url_video(url=f"{records_types['download_url']}")
                            video = requests.get(url=recording_shared_screen[0]['download_url'],stream=True,headers={
                                'Authorization':'Bearer {}'.format(tokens[0])
                            })

                            # Guardar el progreso de descarga
                            download_progress = 0

                            # Definir el tamaño del búfer para leer los datos
                            buffer_size = 1024
                            #Se encapsula en un try por si ocurren errores inesperados al descargar la reunion
                            
                            try:
                                for data in video.iter_content(chunk_size=buffer_size):
                                    zoom_record.write(data)
                                    
                                    # Actualizar el progreso de descarga si hay un tamaño de archivo válido
                                    if  recording_shared_screen[0]["file_size"] > 0:
                                        download_progress += len(data)
                                        # Calcular el porcentaje de descarga
                                        percentage_progress  = (download_progress / recording_shared_screen[0]["file_size"]) * 100
                                        # Imprimir el porcentaje de descarga
                                        print(f"Progreso de descarga de la descarga: {percentage_progress :.2f}%\n")

                                #para descargar el video necesito obtener la url, lo que sucede es que zoom crea un array de dicionarios, con el tipo de grabacion que es, el chat, el audio y el video
                                #necesito filtrar esto
                                print(f"En el folder {record_folder} se descargara la grabacion de la url: {recording_shared_screen[0]['download_url']}\n")
                                
                                
                                
                            except Exception as e:
                                error = str(e)
                                load_json_error(error)
                                return f"No se pudo guardar el video ya que ocurrio esto: {e}"
                            
                            #Una vez se haya descargado correctamente el video, se hara la solicitud para enviarlo al draft del cloud de zoom
                            else:
                                
                                print("Se descargo correctamente el video \n")
                                

                                #intenta enviar al draft del cloud la reunion desde la api de zoom, una vez el archivo es descargado
                                try:

                                        delete_recording = requests.delete(url="https://api.zoom.us/v2/meetings/{}/recordings/?delete=trash".format(response_json["meetings"][record]['id']),headers=self.get_header_access_token_params())
                                        
                                        #Se hacen 2 diccionarios, incluyendo la informacion del video y del cliente para el proceso de subida en el drive
                                        video_info = {
                                            'video_file_name':"Grabacion de la reunion de {}.mp4".format(fecha_folder.date()),
                                            'video_src':os.path.join(record_folder,"grabacion.mp4")
                                        }
                                    
                                        client_info_details = {
                                            'email':clienta_info[0]['email'],
                                            'client_folder_name':clienta_info[0]['nombre']
                                        }
                                        upload_zoom_video(video_info,client_info_details)
                                        
                                        delete_recording.raise_for_status()
                                        
                                except requests.exceptions.HTTPError as e:
                                    error = str(e)
                                    load_json_error(error)
                                        
                                    print("No se pudo eliminar la reunion debido a que: {}\n".format(delete_recording.json()))
                                        
                                    return "No se pudo eliminar la reunion debido a que: {}\n".format(delete_recording.json())                      
        else:
            #Se retorna el error
            return self.clients[1]
        
        
        
    #Espera una lista de clientes y va a comparar el id de la reunion con el meeting_id, para asi saber a que cliente pertenece esa reunion
    def get_client_by_meeting_id(self,clients,meeting_id):
        client = [(cliente) for cliente in clients if cliente['reunion_id'] == meeting_id]
        return client
