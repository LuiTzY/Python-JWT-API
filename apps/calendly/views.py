from .models import Calendly
from .services import CalendlyService
from rest_framework import status
from apps.clients.models import Mentor
from django.db import IntegrityError
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import CalendlySerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication


"""
    1: Las vistas basadas en clases solo aceptara los metodos que tengan definidos en ellas mismas, por lo que si se intenta algunoq que no este respondera con metodo not allowed
    
    El proceso de las solicitudes de informacion a las apis de zoom y drive, siempre sera desde el back por temas de seguridad,
    ya que si al front le enviamos las credenciales para hacer las solicitudes a la api de zoom por ejemplo, estas se verian expuesta
    lo que seria una mala practica y problemas de seguridad
"""


#Vista para manejar el tema de las credenciales de una cuenta de zoom que autorizo una app
class CalendlyCredentialsView(APIView):
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
      
       
        calendly_token = Calendly.get_calendly_token_by_mentor(mentor)
        
        if calendly_token == None:
            return Response({"message":"You dont have a calendly token registered"})
        
        #ya que si existe un token de calendly, se lo pasamos al servicio para que la solicitud 
        calendly = CalendlyService(calendly_token)
        
        calendly_account_details = calendly.get_calendly_user_information()
        
        return Response({"account_details":calendly_account_details})

            
    def post(self,request,format=None):
        
        calendly_token = request.data.get('calendly_token',None)
        
        mentor = Mentor.get_mentor(request.user)
        
        if mentor == None:
            #Si no existe es xq si hay un correo relacionado a una cuenta, pero el usuario no ha auntenticado la app de zoom
            return Response({"error":"You must be a mentor to have this funcionality"},status=status.HTTP_403_FORBIDDEN)
        
        
        #Verificamos si hay un token enviado
        if not calendly_token:
            return Response({"error": "Miss Calendly token"}, status=status.HTTP_400_BAD_REQUEST)
        
        
        
        calendly = CalendlyService(calendly_token)
        #antes de responder verficaremos si el token es valido haciendo una solicitud a calendly
        test_if_valid_token = calendly.test_token()
        
        
        if not test_if_valid_token:
            return Response({"message":"Invalid calendly token"},status=status.HTTP_403_FORBIDDEN)
        
        #antes de guardar el token, se verificara a ver si ya tiene uno relacionado, para que asi no se creen mas registros
        find_calendly_token = Calendly.get_calendly_token_by_mentor(mentor)
        
        if find_calendly_token:
            return Response({"message":"you already have an token delete it o udpated it if you whant to change it"},status=status.HTTP_400_BAD_REQUEST)
        #Al ser valido lo guardamos, pasandole los datos al serializer
        data_serializer = {
            "calendly_token":calendly_token,
            "mentor":mentor.id
        }
        
        calendly_serializer = CalendlySerializer(data=data_serializer)
        if calendly_serializer.is_valid():
            calendly_serializer.save()
            
            return Response({"message":"You Relationed your calendly account succesfully"},status=status.HTTP_200_OK)

            
            #si es false, es xq el token no es valido, xq lo que no se guardara
        return Response({"error":calendly_serializer.errors},status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self,request,format=None):
        
        #Intentaremos obtener las credenciales de una cuenta de zoom
        mentor = Mentor.get_mentor(request.user)
        
        if mentor == None:
            return Response({"error":"You must be a mentor to delete your calendly token"},status=status.HTTP_404_NOT_FOUND)
        
        mentor_calendly_to_delete = Calendly.delete_instance_by_mentor(mentor)
        
        if not mentor_calendly_to_delete:
            return Response({"error":"Maybe a unexpected error"},status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        #aqui ya ha sido borrado
        return Response({"message":"you deleted your calendly credentials successfully"},status=status.HTTP_200_OK)
    
   #se puede hacer una vista para tirarle los eventos agendandos y si son clientes tirarle informacion adicional, es decir (si ya estan registrados en la base de datos)