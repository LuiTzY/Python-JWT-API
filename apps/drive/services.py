from .models import *
from apps.clients.models import Mentor
import uuid
import httpx
import os
from dotenv import load_dotenv
import asyncio
from asgiref.sync import sync_to_async
load_dotenv()

state = str(uuid.uuid4())


class DriveAuthService():
    
    def __init__(self,auth_code,mentor):
        self.headers = ""
        self.auth_code = auth_code 
        self.mentor = mentor
        #Desde que se instancie la clase,
        
    #metodo para obtener las cabeceras para hacer la solicitud de un token de acceso y refresh_token, con un codigo de autorizacion
    def get_headers_for_token(self):
        
        return {
            "Host": "oauth2.googleapis.com",
            "Content-Type": "application/x-www-form-urlencoded",
            "code":self.auth_code,
            "client_id":os.getenv("DRIVE_CLIENT_ID"),
            "client_secret":os.getenv("DRIVE_CLIENT_SECRET"),
            "redirect_uri":os.getenv("DRIVE_REDIRECT_URI"),
            "grant_type":"authorization_code"
        }
        
        
    async def get_access_token(self):
        print(self.get_headers_for_token())
        try:
            print(f"Se hara la solicitud para obtenre las credenciales de drive del mentor {self.mentor.name} \n")
            async with httpx.AsyncClient(params=self.get_headers_for_token()) as client:
            
            #hacemos la solicitud con la instancia del client que ya incluye las cabeceras
                response = await client.post(url="https://oauth2.googleapis.com/token")
                
                if response.status_code == 401 or response.status_code == 403:
                    print("Es invalido no debe de seguir \n")
                    return {"error":"Invalid authorization code"}
                
                
                print(response.status_code)
                print(response.text)
                #credentials = response.json()
                
                return {"message":"saved","credentials":response.json()}
            
                #retornamos un mensaje de que las credenciales se guardaron correctamente

        except httpx._exceptions.HTTPError as e:
            print("Ocurrio un erro http y no se pudo autorizar al usuario\n")
            #retornamos el error ocurrido
            return {"error":f"{e}"}
    
    async def drive_service(self):
        
        #Va a ejcutar la funcion asyncronica para obtener el token de acceso 
        result = await self.get_access_token()
        return result
        
    

        
        
"""
    Porque TokenAuthTransport hereda de AsyncBaseTransport y la instancia que pasamos en el drive service es de este misma
    TokenAuthTransport estamos definiendo nuestro propia capa de transporte, por lo que requiere de una serie de configuraci
    nes y metodos por defecto
"""

class TokenAuthTransport(httpx.AsyncBaseTransport):
    
    def __init__(self, auth_service):
        self.base_transport = httpx.AsyncHTTPTransport() #instancia para poder hacer solicitudes desde un transportador
        self.auth_service = auth_service
        
    
    #metodo asincrono que se encargara de enviar la informacion (recordar que un transportador es el que envian nuestras solicitudes)
    async def handle_async_request(self,request):
        
        print("Hola esto se ejecuto \n")
        #cantidad de intentos actuales
        retries_try = 0
        #cantidad maxima de intentos
        max_retries = 3
        
        #iteramos hasta obtener los maximos intentos
        while retries_try < max_retries:
            
            print(retries_try)
            print("Se agregan los parametros de autorizacion")
            print(f"{self.auth_service.credentials}")

            #se agregara el token a las cabeceras de la solicitud (estamos configurando como sera enviada nuestra solicitud recibida por la instancia del cliente creado) 
            request.headers['Authorization'] = f"Bearer {self.auth_service.credentials.access_token}"
            #haremos la solicitud
            print(f"Esta es la url  de solicitud {request.url} \n")
            #hacemos una solicitud con nuestro base_transport para el manejo de la respuesta que enviara mi transporte personalizado
            
            """
                Mejor explicacion, al mi transportador estar hecho para enviar y recibir solicitudes, este no esta diseñado para el
                manejo de una solicitud no autorizada, por lo que mediante base_transport puedo hacer una solicitud a la ya hecha
                por el cliente, esto me permite interceptar por asi decirlo el resultado de la solicitud antes de ser enviado como
                respuesta al cliente, mediante la respuesta que yo obtenga sabre si tendre que renovar el token
                
                En si lo que se hace es interceptar una solicitud ya hecha para hacer otra solicitud y verificar respuestas
                para tomar determina accion para que mi transportador devuelva la informacion correcta
            """
            response = await self.base_transport.handle_async_request(request)
            
            #una vez obtenida la respuesta verificaremos el codigo de estado para determinar si sera necesaria renovar el token
            if response.status_code == 401:
                print(f"La solicitud se hizo con exito, pero el token es invalido, lo actualizaremos ahora \n")
                await self.auth_service.fetch_token()
                retries_try += 1

                #tener en cuenta que nunca se devolvera un 401 de no autorizado, sino que se intentara hacer la llamda
                
            #retornamos la respuesta
            else:
                print(f"Recibimos otro codigo de estado, veamos cual es {response.status_code} \n")
                return response
        
        #una vez se termina el bucle, devolveremos la ultima respuesta que obtuvimos
        return response
    
    

class DriveService():
    def __init__(self,mentor,endpoint):
        self.credentials = Drive.get_drive_credentials_by_mentor(mentor)
        self.headers = ""
        self.endpoint = endpoint
        self.mentor = mentor
        #base_transport sera una instancide de una capa de transporte asyncrona para manejar solicitudes 
        print(f"CREDENCIALES  OBJETO {self.credentials} \n")
        
    def get_headers(self):
        
        if self.credentials == None:
            return None
        
        return {"Authorization":f"Bearer {self.credentials.access_token}"} 
    
    def get_headers_for_refresh_token(self):
        if self.credentials == None:
            return None
        #aqui explicacion de xq utilizar esta estructura para el actualizar un token https://developers.google.com/identity/protocols/oauth2/web-server?hl=es-419#httprest_3
        return {
            "Content-Type":"application/json",
            "client_id":os.getenv("DRIVE_CLIENT_ID"),
            "client_secret":os.getenv("DRIVE_CLIENT_SECRET"),
            "redirect_uri":os.getenv("DRIVE_REDIRECT_URI"),
            "refresh_token":self.credentials.refresh_token,
            "grant_type":"refresh_token",
            "access_type":"offline"
        }
            
    async def handle_async_req(self,endpoint):
        
        print("Se ejecutara esta funcion \n")
        #fn debe de ser el nombre de una funcion de la clase
        result = await self.get_drive_req(endpoint)
        
        return result
    
    #metodo para obtener nuevamente las credenciales mediante un refresh_token
    async def fetch_token(self):
        # se hara una solicitud asyncrona igualmente para obtenerlo, ya que desde aqui no tendremos un error por asi decirlo no necesitaremos una capa de transporte
        
        async with httpx.AsyncClient() as client:
            print("Intentaremos actualizar")
            #esperamos que se haga la solicitud por post
            response = await client.post("https://oauth2.googleapis.com/token", data=self.get_headers_for_refresh_token())
            
            print(f"Sucedio esto al intentar actualizar {response.status_code}  {response.text} \n")
            #lanzamos una excepcion si ocurrio, ya se por clientes invalidos etc
            response.raise_for_status()
            
            #guardamos las credenciales en formato json, para extraer del diccionario para guardarlas 
            credentials = response.json()
            
            print("Haremos algo con las credenciales \n")
            #obtenemos una instancia del objeto drive del mentor existente
        
            print(f"Credenciales obtenidas de una instancia {credentials}\n")
            self.credentials.access_token= credentials['access_token']
            
            #guardamos las credenciales
            await asyncio.to_thread(self.credentials.save)
            
            #asignamos la instancia con las credenciales actualizadas a self.credentials para nuevas solicitudes
            self.credentials = self.credentials
            
            print("Se Actualizo el token correctamente: \n", self.credentials)


        
    async def get_drive_req(self, endpoint):
        """
            aqui necesitaremos la capa de transporte de token auth, para handlear posibles errores que ocurran en nuestra solicitud y
            le pasamos la instancia de httpx.AsyncHTTPTransport() mediante base_transport, esto xq tiene los metodos necesarios para
            handlear una solicitud que hagamos mendiante el y pasamos el objeto de self, que es la instancia de la clase de auth service
            para poder acceder a las credenciales
        
        """
        async with httpx.AsyncClient(transport=TokenAuthTransport(self)) as client:
            try:
                response = await client.get(endpoint)
                response.raise_for_status()
                return {"response": response.json()}
            except httpx.HTTPError as e:
                return {"error": f"{e}"}
    
    async def create_client_drive_folder(self,client_info):
        file_metadata = {
        "name": f"{client_info['name']} ", # aqui va el nombre del cliente perced
        "mimeType": "application/vnd.google-apps.folder",
        'parents':''#id del folder donde ira todos los clientes
        }

        #en el response de la solicitud se encontrara el id de la carpeta creada
        #luego creamos el registro de la clienta en la base de datos, guardando el id de su folder para su posterior uso
        async with httpx.AsyncClient(transport=TokenAuthTransport(self)) as client:
            response = client.post(url=self.endpoint,headers=self.headers, data=file_metadata)
            response.raise_for_status()
            #Se devuelve el id del folder creado para luego con este ser guardado
            try:
                ClientDrive.objects.aget_or_create(
                mentor = self.mentor,
                client = client_info['client_info']['client_db_id'],
                folder_id = response['id'],
                folder_name = client_info['name'] 
            )
            except Exception as e:
                print(f"Ocurrio este error al intentar crear el cliente {e} \n")
                return
            
            return {"created":{response['id']}}
        
    async def post_drive_req(self, endpoint):
        """
            aqui necesitaremos la capa de transporte de token auth, para handlear posibles errores que ocurran en nuestra solicitud y
            le pasamos la instancia de httpx.AsyncHTTPTransport() mediante base_transport, esto xq tiene los metodos necesarios para
            handlear una solicitud que hagamos mendiante el y pasamos el objeto de self, que es la instancia de la clase de auth service
            para poder acceder a las credenciales
        
        """
        data = {
            "uploadType":"resumable",
            "title":"prueba.txt",
            'mimeType': 'video/mp4',
            'parents':''#aqui va el id del folder de la clienta que se haya creado
        }
        headers = {
        'Authorization': f'Bearer {self.credentials.access_token}',
        'Content-Type': 'application/json; charset=UTF-8',
        'X-Upload-Content-Type': 'video/mp4',  # Tipo MIME del contenido del archivo
        'X-Upload-Content-Length': 'TAMANO_DEL_ARCHIVO_EN_BYTES'  # Tamaño del archivo que se va a subir
                    }
        async with httpx.AsyncClient(transport=TokenAuthTransport(self)) as client:
            try:
                response = await client.post(endpoint)
                response.raise_for_status()
                return {"response": response.json()}
            except httpx.HTTPError as e:
                return {"error": f"{e}"}
           
    async def handle_create_folder(self,client_info):
        print("LLAMAMOS LA FUNCION PARA CREAR EL FOLDER \n")
        result =  await self.create_client_drive_folder(client_info)
        return result
    async def handle_async_post_req(self,endpoint):
        
        print("Se ejecutara esta funcion \n")
        #fn debe de ser el nombre de una funcion de la clase
        result = await self.post_drive_req(endpoint)
        
        return result 
        """
            Al utilizar un transport en un asyncClient lo que hacemos es decir que nuestra solicitud
            sera manejada por esa capa de transporte, que al final lo que hace es la entrega de datos
            recibidos por el servidor de zoom, por eso es que se utiliza ya que si se obtiene un 401
            al momento de hacer una solicitud este en vez de devolvernos nuestro 401 con el contenido
            lo que hara es intentar renovar el token para asi entregar la respuesta correcta.
        """
        

"""
    Se creara una capa de transporte para el manejo de la respuesta de las solicitudes hechas mediante la instancia de un cliente
    cuando usamos una capa de transporte propia, esta se utiliza mendiante un cliente  async with httpx.AsyncClient(transport=TokenAuthTransport(self.base_transport, self)) as client
    debido a esto podemos acceder a esa solicitud  e manejar la respuesta que sera devuelta
    si una capa de transporte no es especificada, esta aun asi usara una por defecto, que lo que hace es siempre retoranos los datos recibidos de la solicitud hecha,
    por eso es que al ser especificada mediante un metodo de la clase handle_async_request tiene nuestra solicitud

"""



