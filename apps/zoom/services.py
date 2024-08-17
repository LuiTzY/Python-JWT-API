import os
import base64
from datetime import datetime
import requests
from .models import Zoom
from dotenv import load_dotenv
from apps.clients.models import Client
from django.db import IntegrityError
from apps.errors.models import ZoomRecordingError
from apps.calendly.services import CalendlyService
import httpx
import asyncio

from apps.drive.services import TokenAuthTransport
load_dotenv()

class ZoomConfig():
    def __init__(self):
        self.clientID = os.getenv("clientID")
        self.clientSecret = os.getenv("clientSecret")
        self.redirectURL = os.getenv("redirectURL")
    
#Clase encargada de la autorizacion de un app de zoom via un code de autorizacion
class ZoomAuthService(ZoomConfig):
    #Esta clase heredara de zoom config para poder acceder a las configuraciones necesarias
    def __init__(self,auth_code):
        super().__init__()

        self.zoom_token_url = 'https://zoom.us/oauth/token/'
        self.auth_code = auth_code
        
    #se le debe de pasar el codigo de autorizacion para la solicitud 
    def zoom_token_auth_params (self):
       #esta funcion devuelve los parametros que van en el header de la solicitud que se le hara a la api de zoom, son necesarioas ya que zoom utiliza el estandar Oauth 2.0
       #para obtener un token de acceso
        return {
            'grant_type': 'authorization_code',  
            'code': self.auth_code, #codigo de autorizacion
            'redirect_uri': self.redirectURL, #url indicada para el manejo de la autorizacion
            'client_id': self.clientID, #client id de zoom generado
            'client_secret':self.clientSecret  #cliente secret de la app de zoom generada
        }

    #metodo para unir el clientID y clientSecret, encondeados en base 64
    def encode_app_credentials(self):
        """se encodean en base 64, el client secret de la app y el client id, para formar uno solo
        esto es debido a que zoom lo requiere para la  hora de hacer la solicitud por post
        ya que los datos son sensibles y deben estar en un formato seguro para luego ser examinados correctamente"""
        auth =  f"{self.clientID}:{self.clientSecret}"
        auth_encode = auth.encode("ascii")
        auth_b64 = base64.b64encode(auth_encode)
        auth_value = auth_b64.decode("ascii")
        #retorna el valor 
        return auth_value
    

    #Este metodo se va a ejecutar cuando haya un post en el api view de zoom
    async def get_access_token(self):
        
        # Hacemos una solicitud POST a la url para obtener el token de acceso, refresh token y otras opciones como el scope etc
        """
            Parametros a enviar
            1. Codigo de autorizacion para ser intercambiado por un access token y refresh_token
            2. Cabeceras necesarias para hacer la solicitud indicado encodeando como autorizacion el client id y client secret en base64 (zoom indica que debe de ser asi)
        """
        
        try:
            
            async with httpx.AsyncClient(headers=self.get_authorization_header(),params=self.zoom_token_auth_params()) as client:
                response = await client.post(self.zoom_token_url)
                
                #si ocurrio un error con la solicitud, lanzara un error para que la excepcion lo capture
                response.raise_for_status()
                
        except httpx.HTTPError as e:
            
            print(f"Ocurrio un Error de autorizacion codigo invalido {e} \n")
            #e es el error que ha ocurrido, y 1 significa que la solicitud se proceso pero hubo un error con el codigo de autorizacion de zoom para la app (es invalido)
            return {"status":response.status_code, "error":f"{e}"}
        
        else:
            #Devolvemos las credenciales para que estas se procesen y se guarden al mentor relacioando, devolvemos un codigo de estado indicando el estatus de mi solicitud
            return {"status":response.status_code, "credentials":  response.json()}

        
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









class ZoomService():
    def __init__(self,mentor):
        self.credentials = self.get_credentials_from_mentor(mentor)
        #instancio la clase y automaticamente se inicia la conexion a la base de datos
        self.zoom_token_url = 'https://zoom.us/oauth/token/'
        self.zoom_refresh_token_url = 'https://zoom.us/oauth/token/'
        self.clientID = os.getenv("clientID")
        self.clientSecret = os.getenv("clientSecret")
        self.redirectURL = os.getenv("redirectURL")
        self.storage_url = "D:/Zoom Grabaciones/"
        self.calendly = None
        self.clients = ""
        self.mentor = mentor
        
    #Desde que la clase sea instanceada obtendremos las credenciales asociadas a ese mentor
    def get_credentials_from_mentor(self,mentor):
        print("Se ejcutara el meotod para obtener las credenciales por un mentor \n")
        credentials = Zoom.get_zoom_credentials_by_mentor(mentor)
        return credentials
      
    
  #metodo para unir el clientID y clientSecret, encondeados en base 64
    def encode_app_credentials(self):
        """se encodean en base 64, el client secret de la app y el client id, para formar uno solo
        esto es debido a que zoom lo requiere para la  hora de hacer la solicitud por post
        ya que los datos son sensibles y deben estar en un formato seguro para luego ser examinados correctamente"""
        auth =  f"{self.clientID}:{self.clientSecret}"
        auth_encode = auth.encode("ascii")
        auth_b64 = base64.b64encode(auth_encode)
        auth_value = auth_b64.decode("ascii")
        #retorna el valor 
        return auth_value
    
    #este metodo devolvera los parametros necesarios en la cabecera de la peticion para la autorizacion incluira el token de accesso
    def get_header_access_token_params(self):
        print("Se supone que sta el token aqui {}".format(self.credentials))
        return {
            'Authorization': 'Bearer {}'.format(self.credentials.access_token)
        }
    
    def refresh_token_params(self):
        #Retornamos los parametros necesarioas para obtener unas nueveas credenciales desde zoom
        return {
                    'grant_type':'refresh_token',
                    'refresh_token':self.credentials.refresh_token
                }

        
    async def fetch_token(self):
        
        try:
            #Hacemos una solicitud para refrescar el token, con los parametros necesarios
            async with httpx.AsyncClient(headers=self.refresh_token_headers(), params=self.refresh_token_params()) as client:

                response = await client.post(url=self.zoom_refresh_token_url)
                        
                #Invocamos un error si realmente este ocurre con la solicitud
                response.raise_for_status()
            
        except  httpx.HTTPError as e:
            #imprimer el error por consola
            print(f"Error: No se pudo actualizar el token de accesso debido a: {response.text} \n")
            #retornamos el error junto a un numero 2, que identifca que ocurrio un error con la solicitud
            return {"status":response.status_code, "error":f"{e}"}
        
        else:
            #Obtenemos las credenciales correctamente y las actualizamos a la instancia del mentor asociado
            try:
                credentials = response.json()
                
                #A la instancia de los tokens que obtuvimos le asigamos las nuevas credenciales que obtuvimos
                self.credentials.access_token = credentials['access_token']
                self.credentials.refresh_token = credentials['refresh_token']
                
                #Ejecutamos la operacion de guardar esto en un hilo aparte porque puede demorar
                self.credentials.save()
                #Asignamos la instancia de las credenciales nuevamente (por si acaso no las toma correctamente)
                self.credentials = self.credentials
                
                print(f"Se guardaron las credenciales correctamente para el mentor {self.credentials.mentor.name}\n")
                
            except Exception as e:
                #retornamos un error ocurrido al intentar guardar en las bd
                return {"error_type":"database_error","error":f"{e}"}
            
            return {"status":"200"}
        

    #Metodo que devuelve las cabeceras necesarias al momento de hacer una solicitud de actualizacion de un token
    def refresh_token_headers(self):
      return {
        "Host":"zoom.us",
        #Authorization, lleva la estructura de Basic + los tokens codificados en base a 64 bits, zoom lo requiere asi para su peticion
        "Authorization": f"Basic {self.encode_app_credentials()}",
        #el tipo de dato que espera la api de zoom para la solicitud
        "Content-Type": "application/x-www-form-urlencoded",
        }
    
    async def get_zoom_req(self,endpoint):
      
        print(f"Haremos una solicitud a: {endpoint} con el mentor :{self.credentials}")
        try:
            
            #hacemos una solicitud por get al endpoint que nos pasen, y obtenemos los params de las cabeceras
            async with httpx.AsyncClient(transport=TokenAuthTransport(self)) as client: 
                response = await client.get(url=endpoint,headers=self.get_header_access_token_params())
            
                #print(f"Esto son los datos con los que se hara la solicitud {endpoint} cabeceras de la solicitud {self.header_access_token_params}")
                response.raise_for_status()
            
        except httpx.HTTPError as e:
            return {"error_type":"HTTPError", "error":f"{e}","status":response.status_code}
        
        else:
            return {"status":response.status_code,"response":response.json()}
            
    async def get_response_zoom_req(self,endpoint):
        response = await self.get_zoom_req(endpoint)
        print(f"Respuesta obtenida {response }\n")
        return response
    
    def get_storage(self):
        try:
            if os.path.exists(self.storage_url):
                print("El directorio esta disponible para guardar las grabaciones de los clientes. \n")
                return True
        except FileNotFoundError:
            # error = ZoomRecordingError.objects.create(error="FileNotFoundError")
            
            print("El directorio no se encuentra debido a que el disco duro externo no está conectado. \n ")
            return False
        
        except Exception as e:
            error = str(e)
            # er = ZoomRecordingError.objects.create(error=error)
            print(f"Ocurrio un error inesperado \n")
            
            return False
        
    def download_zoom_recordings(self,start_date,end_date,mentor,calendly_token):
        
        #asignamos a los clientes la instancia de la clase de calendly junto con el token recibido, debido a esto sabra siempre a quien pertenecera la informacion
        self.calendly = CalendlyService(calendly_token)
         # Convertimos las fechas a cadenas en el formato correcto
        start_date_str = start_date.strftime("%Y-%m-%dT%H:%M:%S.000000Z")
        end_date_str = end_date.strftime("%Y-%m-%dT%H:%M:%S.000000Z")
        self.clients = self.calendly.get_scheduled_events_invite_email(start_date_str,end_date_str)
        
        #lista de grabaciones que se enviaran para descargar asincronicamente junto con la informacion del cliente que pertenece etc
        recordings_info = []
        
        
        """
            Se hara una sola solicitud para obtener las grabaciones, junto con las clientes que esten y no esten asociadas a una
            desde la fecha inicial (dada) hasta la fecha final que es 7 dias + la actual
            
            Dependiendo de la cantida de grabaciones que se encuentren, se tomara una u otra funcion que al final cumplen con el mismo
            objetvio de devolver una seride clientes y grabaciones asociados y no asociados
            
            Este proceso siempre sera el mismo, se hara una solicitud a la api de calendly para obtener los eventos que son hechos por (clientes),
            cada evento tiene un id de una reunion de zoom, cuando esto sucede ya la grabacion debera de estar subida
            en la nube de zoom, por lo que esta debera de coincidir con alguno de los clientes asociados a ese id de reunion de zoom de la grabacion
            Si la grabacion no esta, simplemente no se tomara en cuenta a la hora de que zoom nos devuelva las graabaciones para esa fecha ya que no ha sido subida
            
            Con esto asociamos un cliente con una grabacion, una vez esto es obtenido se creara un registro de ese cliente en la base de datos,
            con su nombre y su correo electronico que haya puesto en calendly,
            una vez suceda esto se descargara la grabacion en el disco duro en la ruta indicada, con el nombre de carpeta de la fecha de ese grabacion en si, luego se hace una solicitud para
            enviar al draft esa grabacion de zoom una vez es decargada correctamente (aqui hay que validar ciertos casos: Se descargue correctamente, no se descargue correctamente, no encuentre
            la ruta es decir el (disco duro, que la excepcion seria FileNotFoundError), cualquier caso que ocurra debe de ser guardado en la base de datos, en los casos en que ocurran
            errores el flujo del programa se debe de detener y no seguir
            
        """
        #Pasamos los clientes en un contexto asyncronico para poder trabajarlos de manera correcta y que no nos devuelva una corutina si no el objeto directamente
        clients = asyncio.run(self.get_zoom_req("https://api.zoom.us/v2/users/me/recordings?from={}&to={}".format(start_date,end_date)))
        print(f"CORUTIMA CLIENTES {clients} \n")        
        #se convierten los datos en formato json de la respuesta de la api de zoom, para poder acceder a ellos y manejarlos           
        
        
        
        #print("Se obtuvieron esta cantidad de grabaciones de la fecha: {} grabaciones encontradas: {}\n".format(start_date.strftime("%Y-%m-%d"),clients[1]['total_records']))
        
        
        #Se consulta el status del disco duro, para ver si esta conectado en la computadora o no, para verificar si las grabaciones pueden ser guardadas
        storage_status = self.get_storage()
        
        #Verificamos la disponibilidad del disco duro
        if not storage_status:
            return {"disk_status":"No disponible"}
        
        #El disco duro esta disponible para almacenar las carpetas
        print("El disco duro se encuentra para descargar las grabaciones \n")   
            
        
            
            #accedemos a la respuesta al total de grabaciones, para determinar que funcion sera utilizada para descargar las grabaciones
        print("Se obtuvieron las grabaciones desde la api de zoom correctamente \n")
        #Si solo hay una reunion, se utilizara el metodo para obtener la informacion de esa sola reunion 
        if clients['response']['total_records'] == 1:
            
            print(f"Obtuvimos una sola grabacion dentro del rango de fechas establecido {start_date} {end_date}\n")
            #devuelve la un diccionario de la grabacion
            record = self.get_one_recording_full_info(clients['response']) 
            recordings_info.append(record)
            
        elif clients['response'][1]['total_records'] > 1:
            print(f"Obtuvimos varias grabaciones dentro del rango de fechas establecido {start_date} {end_date}\n")
            #Si hay mas de una reunion entrara aqui y devolvera una lista de diccionarios de la grabaciones con la informaciones
            recordings = self.get_multiple_recordings_full_info(clients['response'])
            recordings_info.append(recordings)

        else:
            print("No se encontraron grabaciones")
        return {"records_found":len(recordings_info),"records_info":recordings_info }
            

            
                        
            
    
    def get_one_recording_full_info(self, response_json): #response_json va a ser la respuesta de la api de zoom                          
                
                
                print(f"Obteniendo informacion de la grabacion {response_json} \n")
                
                #Esta funcion solo devolvera la informacion de la grabacion, cliente al que pertenece, grabacion, donde se descargara etc
                #La subida de drive sera otro tema a evaluar luego de descargar las grabaciones                
                print(f"Clientes Obtenidos {self.clients} \n")

                #verificamos que respuesta obtuvimos de los metodos de calendly para mejorar la captura de errores
                if self.clients[0] == 1:

                    #Obtenemos loc clientes y hacemos el proceso de la automatizacion
                    #guardamos la informacion de la clienta que coincida con el id de la reunion relacionado
                    clienta_info = self.get_client_by_meeting_id(self.clients[1],response_json["meetings"][0])

                    #verficamos si la grabacion tiene una clienta relacionada
                    if 'not_found_client' in clienta_info:
                        #retoranomos solo la informacion de la grabacion
                        return clienta_info
                    
                    
                    #caso contrario retornamos la informacion completa de la clienta
                    return clienta_info 
                
                else:
                    #Retornamos el error
                    return self.clients[1]
                    
                        
                            
    def get_multiple_recordings_full_info(self,response_json):
        
        print("Obtuvimos varias grabaciones \n")
        print(f" Clientes   {self.clients}\n")
        
        if self.clients[0] == 1:
                recordings = []
                records = []
                banned_recordings_id = []              
            #si son mas de una grabacion las que se encuentren en el rango de esas fechas y los ids de estas no estan en los ids baneados
                for record in range(response_json["total_records"]):
                    
                    if response_json["meetings"][record]['uuid'] not in banned_recordings_id:
                        banned_recordings_id.append(response_json["meetings"][record]['uuid'])
                        records.append(response_json["meetings"][record])
                
                """
                    De la lista de clientes que se obtenga de la fecha dada, se van a comparar los ids de las reuniones de zoom
                    para ver cuales clientes tienen una reunion de zoom en la nube
                """
                clients_info = self.get_client_by_meetings_ids(self.clients[1],records)
                print(f"Reuniones varias obtenidas {clients_info} \n")
                return clients_info                   
        else:
            #Se retorna el error
            return self.clients[1]
        
        
        
    #Espera una lista de clientes y va a comparar el id de la reunion con el meeting_id, para asi saber a que cliente pertenece esa reunion
    def get_client_by_meeting_id(self,clients,meeting):
        
        for cliente in clients:
            
            if cliente['reunion_id'] == meeting['id']:
                
                    client_instance = Client.get_client(cliente['email'])
                    #si no obtenemos una instancia, es decir none, creamos el cliente
                    if client_instance == None:
                        client_instance= Client.objects.create(name=cliente['nombre'],email=cliente['email'],mentor=self.credentials.mentor)
                    
                    print("Nombre de la clienta: {} Correo de la clienta: {}".format(cliente['nombre'],cliente['email']))
                    
                    #se creara un folder con el nombre del cliente
                    folder_clienta_name = os.path.join(self.storage_url,cliente['nombre'])
                        

                    #obtenemos la fecha de cuando se inicio la reunion
                    fecha_invalid_format = meeting["start_time"]
                    #la convertimos en un formato valido ya que el tipo de objeto que es la fecha es:"2023-10-02T20:25:55Z"
                    fecha_folder = datetime.strptime(fecha_invalid_format, "%Y-%m-%dT%H:%M:%SZ")
                    
                    #se forma una ruta, para crear una carpeta para esa grabacion en esa ruta, el nombre de la carpeta sera la fecha de la grabacion con un formato DATE Ej(2020-12-12)
                    record_folder = os.path.join(folder_clienta_name,f"{fecha_folder.date()}")
                    
                    cliente['client_db_id'] = client_instance.id
                    client_info = {
                            "client_info":cliente,
                            #informacion de la reunion de la grabacion
                            "client_meeting_details":{
                                
                                "id":meeting['id'],
                                "title":meeting['topic'],
                                "date":meeting['start_time'],
                                "meeting_time":meeting['duration']
                                                    },
                                #Lista de las lista de archivos de las grabaciones, solo almacenara la que es un video y su extension debe der ser MP4 (es necesario, ya que manualmente se tendria que ver)
                                #cual es el indice que tiene ese archivo MP4, y estos indices pueden variar dependiendo si hay archivos de texto o no etc...
                                "client_record_details":
                                    
                                 [
                            #estos son los campos que se agregaran de recording_files en la lista por comprension
                            ({"file_size":media['file_size'],"download_url":media['download_url'],"extension":media['file_extension'],"play_url":media['play_url']})
                            #cada recording_files que se encuentre sera representando como media, y solo se guardara el que su extension sea mp4
                            for media in meeting['recording_files'] if media['file_extension'] == "MP4"
                            
                            ],       
                            "client_folder_details": {"folder_record_name":record_folder,"folder_record_client":folder_clienta_name}
                        }
                    
                    return client_info
            else:
                return {"not_found_client":meeting}
            

    def get_client_by_meetings_ids(self,clients,meetings):
        
        #lista de clientes relacionados a un id de zoom 
        clientes = []
        #Se alamcenan las reuniones de zoom que no tienen a un cliente relacionado en calendly
        zoom_meeting_without_client = [ ]
        #Itero sobre los clients
        for i in range (len(clients)):
            
            #itero sobre las reuniones para compararlo con el cliente que este iterando
            for j in range(len(meetings)):
                #verifico si el cliente que estoy iterando es igual al de la reunion
                if clients[i]['reunion_id'] == meetings[j]['id']:
                    print("Cumplio este \n ")
                    #si lo es, lo agrego
                    
                    
                    client, client_created = Client.objects.get_or_create(name=clients[i]['nombre'],email=clients[i]['email'],mentor=self.credentials.mentor) 
                    #se creara un folder con el nombre del cliente
                    folder_clienta_name = os.path.join(self.storage_url,f"{clients[i]['nombre']}")

                    #obtenemos la fecha de cuando se inicio la reunion
                    fecha_invalid_format = meetings[j]["start_time"]

                    #la convertimos en un formato valido ya que el tipo de objeto que es la fecha es:"2023-10-02T20:25:55Z"
                    fecha_folder = datetime.strptime(fecha_invalid_format, "%Y-%m-%dT%H:%M:%SZ")
                    

                    #se creara una carpeta para esa grabacion, el nombre de la carpeta sera la fecha de la grabacion
                    record_folder = os.path.join(folder_clienta_name,f"{fecha_folder.date()}")
                    date_invalid =datetime.strptime(meetings[j]['start_time'], "%Y-%m-%dT%H:%M:%SZ")

                    client_info = {
                        "client":clients[i],
                        #informacion de la reunion de la grabacion
                        "client_meeting_details":{
                            "id":meetings[j]['id'],
                            "title":meetings[j]['topic'],
                            "date":date_invalid.strftime("%d-%m-%Y"),
                            "meeting_time":meetings[j]['duration']
                                                },
                        #solo se mostrara la informacion de la grabacion que sea un MP4, ya que zoom lo que nos da es una lista con las diferentes media que se crean de la grabacion audio, video etc
                        #se hara un diccionario con ese media incluyendo lo que pesa, la url de descarga etc
                        "client_record_details":[
                            #estos son los campos que se agregaran de recording_files en la lista por comprension
                            ({"file_size":media['file_size'],"download_url":media['download_url'],"extension":media['file_extension'],"play_url":media['play_url']})
                            #cada recording_files que se encuentre sera representando como media, y solo se guardara el que su extension sea mp4
                            for media in meetings[j]['recording_files'] if media['file_extension'] == "MP4"],
                        "client_folder_details":{
                            #nombre del folder donde se guardara la grabacion
                            "folder_record_name":record_folder,
                            "folder_record_client":folder_clienta_name
                        }
                    }
                    
                    clientes.append(client_info)
                else:
                    date_invalid =datetime.strptime(meetings[j]['start_time'], "%Y-%m-%dT%H:%M:%SZ")
                    meet = {
                        "id":meetings[j]['id'],
                        "title":meetings[j]['topic'],
                        "date":date_invalid.strftime("%d-%m-%Y"),
                        "record_details":[
                            #estos son los campos que se agregaran de recording_files en la lista por comprension
                            ({"file_size":media['file_size'],"download_url":media['download_url'],"extension":media['file_extension'],"play_url":media['play_url']})
                            #cada recording_files que se encuentre sera representando como media, y solo se guardara el que su extension sea mp4
                            for media in meetings[j]['recording_files'] if media['file_extension'] == "MP4"
                            
                            ]
                            }
                    zoom_meeting_without_client.append(meet)
                    
                    
        #devolvemos los clientes que tienen una reunion con un evento de calendly, y a los que no se le encontro un evento de calendly
        return {"clients":clientes, "not_found_client":zoom_meeting_without_client}



    