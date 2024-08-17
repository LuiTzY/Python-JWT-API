from .models import Zoom,UserZoomEmail
from .services import ZoomService,ZoomAuthService
from rest_framework import status
from apps.clients.models import Mentor
from django.db import IntegrityError
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import ZoomCredentialsSerializer
from django.core.exceptions import ObjectDoesNotExist 
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
import asyncio

"""
    1: Las vistas basadas en clases solo aceptara los metodos que tengan definidos en ellas mismas, por lo que si se intenta algunoq que no este respondera con metodo not allowed
    
    El proceso de las solicitudes de informacion a las apis de zoom y drive, siempre sera desde el back por temas de seguridad,
    ya que si al front le enviamos las credenciales para hacer las solicitudes a la api de zoom por ejemplo, estas se verian expuesta
    lo que seria una mala practica y problemas de seguridad
"""


#Vista para manejar el tema de las credenciales de una cuenta de zoom que autorizo una app
class ZoomCredentialsView(APIView):
    #Permisos de clases para los tokens JWT utilizados en los endpoints en las cabeceras de la peticion (headers)
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    #Nota: No se utilizara el metodo put para actualizar las credenciales, ya que estas se actualizan solas cada vez que sea necesario en la solicitud 
    
    def get(self,request,format=None):
        print(f"Usuario que hizo la solicitud {request.user.first_name} \n")
        
        #Verficamos si es un mentor el que esta haciendo la solicitud
        mentor = Mentor.get_mentor(request.user)
        if mentor is None:
            #si no lo es retornamos un mensaje de que no puede seguir a menos de que sea un mentor
          return Response({"message":"You must be a mentor to have this functionality"},status=status.HTTP_409_CONFLICT)
      
       #caso contrario, ya que lo es seguira el flujo para ver si tiene un correod e una cuenta de zoom asociada para usar una app
      
        #buscamos el mentor que esta en las credenciales para comparar si es el mismo que se coloco anteriormente
        mentor_zoom_email = UserZoomEmail.get_user_zoom_email(mentor)
            
            
        #capturamos si no existe un email asociado al de una cuenta de zoom, con el usuario que hace la solicitud 
        if mentor_zoom_email == None:
            return Response({"error":"You must have an zoom account email to use an app "},status=status.HTTP_400_BAD_REQUEST)
        
        #si obtenemos un correo de una cuenta de zoom, asociado al usuario que esta haciendo la peticion, haremos la comparacion de correos
        
            
        
        #Buscamos si obtendremmos unas credenciales asociadas para verificar si los correos coinciden, ya que si no, es xq la app no ha sido autorizada hasta el momento
        mentor_credentials = Zoom.get_zoom_credentials_by_mentor(mentor)
        
        if mentor_credentials == None:
            #Si no existe es xq si hay un correo relacionado a una cuenta, pero el usuario no ha auntenticado la app de zoom
            return Response({"error":"Not credentials asociated with this user, you must authorize the zoom app to get your details"},status=status.HTTP_403_FORBIDDEN)
        
        #Siempre se le pasara una instancia de un mentor que si tenga credenciales
        service = ZoomService(mentor)
        
        #obtenemos informacion acerca del correo del cliente, pasandole el endpoint y el mentor que pertenecera al usuario que haga la solicitud al que pertenece la solicitud
        zoom_user_account_info = asyncio.run(service.get_zoom_req("https://api.zoom.us/v2/users/me"))
        
        #verficamos a ver si obtuvimos la informacion correcta ya que devolvera una lista con un numero 3 y los datos si no hubo errores en la misma
        if  'response' in zoom_user_account_info:     
            
            #nota: No es necesario verificar si los correos coinciden ya que al momento de guardar las credenciales esto se verifica
            #enviamos la informacion de la cuenta, ya que si coinciden
            return Response({"zoom_account_details":zoom_user_account_info['response']},status=status.HTTP_202_ACCEPTED)
        
        #caso contrario devolvemos el error
        else:
            return Response({"error":f"Unexpected error ocurred {zoom_user_account_info['error']}"},status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    def post(self,request,format=None):
        
        auth_code = request.query_params.get('auth_code', None)
        mentor = Mentor.get_mentor(request.user)
        
        if mentor == None:
            #Si no existe es xq si hay un correo relacionado a una cuenta, pero el usuario no ha auntenticado la app de zoom
            return Response({"error":"You must be a mentor to have this funcionality"},status=status.HTTP_403_FORBIDDEN)
        
        
         #buscamos el mentor que esta en las credenciales para comparar si es el mismo que se coloco anteriormente
        mentor_zoom_email = UserZoomEmail.get_user_zoom_email(mentor)
            
            
        #capturamos si no existe un email asociado al de una cuenta de zoom, con el usuario que hace la solicitud 
        if mentor_zoom_email == None:
            return Response({"error":"You must have an zoom account email to use an app "},status=status.HTTP_400_BAD_REQUEST)
        
        
        #Verificamos si hay un codigo de autorizacion
        if not auth_code:
            return Response({"error": "Miss Authorization code"}, status=status.HTTP_400_BAD_REQUEST)
        
        print("Se obtuvieron los paramas \n")
        
        #Psamos el codigo de autorizacion
        service = ZoomAuthService(auth_code)
        
        #Tomara el codigo de autorizacion que le pasamos a la instancia e hara la solicitud        
        credentials = asyncio.run(service.get_access_token())
        print(credentials)
        #verificamos si obtuvimos las credenciales
        if 'credentials' in credentials:
            credentials_save = {
                'mentor':mentor.id, #si llega aqui, es xq el user que esta en la req si es un mentor, tambien se podria pasar la instancia del mentor
                'access_token':credentials['credentials']['access_token'],
                'refresh_token':credentials['credentials']['refresh_token']

            }
            
            print(credentials_save)
            #El serializador solo tomara los campos que se hayan definido en el, los demas los ignora
            serializer = ZoomCredentialsSerializer(data=credentials_save)
            
            #verficamos si obtuvimos unas credenciales validas segun se ha definido en el serializador
            if serializer.is_valid():
                print("Credenciales son validas")
                #se guradan las credenciales
                serializer.save()
                
                zoom_service = ZoomService(mentor)
                print(f"Supeustas credenciales obtenidas {zoom_service.credentials} \n")
                #obtenemos informacion acerca del correo del cliente, pasandole el endpoint y el mentor que pertenecera al usuario que haga la solicitud al que pertenece la solicitud
                zoom_user_account_info = asyncio.run(zoom_service.get_response_zoom_req("https://api.zoom.us/v2/users/me"))
                
                #verficamos a ver si obtuvimos la informacion correcta ya que devolvera una lista con un numero 3 y los datos si no hubo errores en la misma
                if 'response'  in zoom_user_account_info:
                    
                    #verficamos si los emails coninciden para dejar las credenciales asociadas a ese usuario
                    if not zoom_user_account_info['response']['email'] == mentor_zoom_email.email:
                        print("Entra aqui ya que no son iguales")
                        #intentamos borrar las credenciales relacionadas al usuario ya que no coinciden, el correo de la app con el de la cuenta de zoom
                        zoom_account_to_delete = Zoom.delete_instance_by_mentor(mentor)
                        if zoom_account_to_delete:
                            #Se borraron las credenciales relacionadas a la del usuario, se devuelve el error
                            return Response({"error":"The zoom email account that you introduced, dont matches with the zoom email account you authorized"},status=status.HTTP_400_BAD_REQUEST)
                        #capturamos el error que oucrrio y los envimos como respuesta
                        #return Response({"error":f"Unexpected error ocurred while trying to delete the user account email{e}"},status=status.HTTP_400_BAD_REQUEST)
                        
                        
                    #enviamos la informacion de la cuenta, ya que si coinciden (las credenciales ya han sido guardadas)
                    return Response({"zoom_account_details":zoom_user_account_info['response']},status=status.HTTP_201_CREATED)
                
                #caso contrario devolvemos el error
                else:
                    return Response({"error":f"Unexpected error ocurred {zoom_user_account_info[0]}"},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
            
            #devolvemos el error que haya ocurrido con el serializador
            return Response({"error":serializer.errors},status=status.HTTP_400_BAD_REQUEST)
        
        return Response({"error":credentials},status=status.HTTP_403_FORBIDDEN)
    
    
    def delete(self,request,format=None):
        
        #Intentaremos obtener las credenciales de una cuenta de zoom
        mentor = Mentor.get_mentor(request.user)
        
        if mentor == None:
            return Response({"error":"You must be a mentor to delete your zoom credentials"},status=status.HTTP_404_NOT_FOUND)
        
        mentor_zoom_credentials_delete = Zoom.delete_instance_by_mentor(mentor)
        if not mentor_zoom_credentials_delete:
            return Response({"error":"Maybe a unexpected error"},status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        #aqui ya ha sido borrado
        return Response({"message":"you deleted your zoom credentials successfully"},status=status.HTTP_200_OK)
    
    
#Vista relacionada a las grabaciones de una cuenta de zoom
class ZoomRecordingsViews(APIView):
    #Permisos de clases para los tokens JWT utilizados en los endpoints en las cabeceras de la peticion (headers)
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def get(self,request,format=None):
        #En los parametros esperamos recibir fechas para buscar las grabaciones que coincidan 
        start_date,end_date = request.query_params.get('start_date',None),request.query_params.get('end_date',None)
        
        mentor = Mentor.get_mentor(request.user)
        
        if mentor == None:
            #Si no existe es xq si hay un correo relacionado a una cuenta, pero el usuario no ha auntenticado la app de zoom
            return Response({"error":"You must be a mentor to have this funcionality"},status=status.HTTP_403_FORBIDDEN)
        
        service = ZoomService(mentor)

        
        if  start_date == None  or  end_date == None:
            return Response({"error":"You Must Provided a start_date o end_date"}, status=status.HTTP_400_BAD_REQUEST)
        
        #Pasamos la respuesta y lo colocamos en una corutina para obtener el resultado, directamente al usar un http transport el token se actualizara si es necesario
        recordings = asyncio.run(service.get_response_zoom_req(f"https://api.zoom.us/v2/users/me/recordings?from={start_date}&to={end_date}"))
        
        #Retornamos las grabaciones
        return Response({"recordings":recordings},status=status.HTTP_202_ACCEPTED)
        
        #Si por casualidad al hacer la solicitud de obtener las grabaciones las credenciales son invalidas y se renuevan
        #hariamos otra vez la solicitud
        

#Vista para manejar las acciones relacionadas con un email relacionado a una cuenta de zoom
class ZoomEmailUserAccount(APIView):
    #Permisos de clases para los tokens JWT utilizados en los endpoints en las cabeceras de la peticion (headers)
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    #Metodo HTTP para crear una guardar un correo de una cuenta de zoom de un usuario 
    def post(self,request,format=None):
        
        
        mentor = Mentor.get_mentor(request.user)
        #mentor =  Mentor.objects.get(user=request.user)
        print(mentor)
        
        if mentor == None:
            return Response({"error":"You must be a mentor to associated an email zoom account"},status=status.HTTP_400_BAD_REQUEST)
        
        #verificaremos si ya tiene un correo de una cuenta de zoom relacionada para que no pueda crear otro
        mentor_zoom_email_account = UserZoomEmail.get_user_zoom_email(mentor=mentor)
        if not mentor_zoom_email_account == None:
            return Response({"message":"You already have an email registered with your zoom account"},status=status.HTTP_403_FORBIDDEN)
        
        #caso contrario de que sea none mentor_zoom_email_account, es que no existe, por lo que se creara 
        try:
            UserZoomEmail.objects.create(email=request.data['email'],mentor=mentor)
        #capturamos si ya existe una cuenta con ese correo
        except IntegrityError:
            return Response({"error":"This email is used already"},status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            #Nota los correos deben de ser unicos para que solo una cuenta de zoom sea asociada
            return Response({"error":f"{e}","message":"Ocurrio un error al intentar registrar el correo de una cuenta de zoom"},status=status.HTTP_400_BAD_REQUEST)
        
        #decimos que la solicitud se proceso, pero internamente el proceso va a demorar su tiempo para ejecutarse
        return Response({"message":"You register succesfully an email zoom account"},status=status.HTTP_202_ACCEPTED)
    
    
    #Metodo HTTP para actualizar un correo de una cuenta de zoom de un usuario
    def put(self,request,format=None):
        
        mentor = Mentor.get_mentor(request.user)
        if mentor == None:
            return Response({"error":"You must be a mentor to associated an email zoom account"},status=status.HTTP_400_BAD_REQUEST)
        
        email = request.data.get('email', None)
        #Verificamos si obtuvimos el email en los datos post de la solicitud
        if not email:
            return Response({"message":"You have to give an user zoom email to update"},status=status.HTTP_403_FORBIDDEN)
        
        zoom_account_email = UserZoomEmail.get_user_zoom_email(mentor)
        #Verificamos si existe una cuenta para actualizar
        if zoom_account_email is None:
            return Response({"error":"You not have an email zoom account to update"},status=status.HTTP_400_BAD_REQUEST)
        
        #verificaremos si ya tiene unas credenciales asociadas a ese correo, por lo que si se borraran y se actualizara, si no pues simplemente actualizara
        #esto se hace para que siempre que se cambie el correo en el caso de que ya se haya autorizado una app, se borren esas credenciales, ya que los correos no van a coincidir
        #no se guarda en una variable ya que no es necesario obtener el estado de esa operacion
        Zoom.delete_instance_by_mentor(mentor)
        
        zoom_account_email.email = email
        
        #Verficamos si ya existe un mentor con ese correo
        verify_zoom_account = UserZoomEmail.get_zoom_by_email(email)
        
        if not verify_zoom_account is None:
            return Response({"Message":"Sorry but we already have an mentor registered with this email"}, status=status.HTTP_400_BAD_REQUEST)
        
        zoom_account_email.save()
        return Response({"message":"your zoom account email was succesfully updated"},status=status.HTTP_202_ACCEPTED)

    #Metodo HTTP para borrar un email asociado a una cuenta de zoom de un usuario
    def delete(self,request,format=None):
        
        mentor = Mentor.get_mentor(request.user)
        if mentor == None:
            return Response({"error":"You must be a mentor to associated an email zoom account"},status=status.HTTP_400_BAD_REQUEST)
        
        zoom_user_email_account = UserZoomEmail.get_user_zoom_email(user=request.user)
        
        if zoom_user_email_account == None:
            return Response({"message":"You dont have an email asociated with your account to delete"},status=status.HTTP_404_NOT_FOUND)
        
        try:
            zoom_user_email_account.delete()
            return Response({"message":"you deleted succesfully your zoom email account"},status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"message":f"Ocurred a unexpected server error while trying to delete the user zoom email account","error":f"{e}"},status=status.HTTP_500_INTERNAL_SERVER_ERROR)