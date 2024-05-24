import datetime
from services import ZoomService
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from .serializers import ZoomCredentialsSerializer,ZoomUpdateCredentialsSerializer


"""
    El proceso de las solicitudes de informacion a las apis de zoom y drive, siempre sera desde el back por temas de seguridad,
    ya que si al front le enviamos las credenciales para hacer las solicitudes a la api de zoom por ejemplo, estas se verian expuesta
    lo que seria una mala practica y problemas de seguridad
"""

service = ZoomService()

class ZoomCredentialsView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def post(self,request,format=None):
        #agregamos el usuario al diccionario de data, ya que el serializador lo espera para ser valido
        request.data['user'] = request.user
        auth_code = request.query_params.get('auth_code', None)
        
        #Verificamos si hay un codigo de autorizacion
        if not auth_code:
            return Response({"error": "Miss Authorization code"}, status=status.HTTP_400_BAD_REQUEST)
        
        credentials = service.get_access_token(auth_code)

        #verificamos si obtuvimos las credenciales
        if credentials[0] == 1:
            #El serializador solo tomara los campos que se hayan definido en el, los demas los ignora
            serializer = ZoomCredentialsSerializer(data=credentials[1])
            
            #verficamos si obtuvimos unas credenciales validas segun se ha definido en el serializador
            if serializer.is_valid():
                #se guradan las credenciales
                serializer.save()
                return Response({"message":"Credentials saved succesfully"},status=status.HTTP_201_CREATED)
            
            #devolvemos el error que haya ocurrido con el serializador
            return Response({"error":serializer.errors},status=status.HTTP_400_BAD_REQUEST)
        
        return Response({"error":credentials[1]},status=status.HTTP_403_FORBIDDEN)
        
    """def put(self,request,format=None):
        
        serializer = ZoomUpdateCredentialsSerializer(request.user,data=request.data)
        if serializer.is_valid():
            #Si es valido el serializador, guardamos las credenciales
            serializer.save()
            return Response({"message":"Credentials Updated Succesfully"},status=status.HTTP_202_ACCEPTED)
        #devolvemos el error que haya ocurrido con el serializador
        return Response({"error":serializer.errors},status=status.HTTP_400_BAD_REQUEST)"""
    
class ZoomRecordingsViews(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def get(self,request,format=None):
        #En los parametros esperamos recibir fechas para buscar las grabaciones que coincidan 
        start_date,end_date = request.query_params.get('start_date',None),request.query_params.get('end_date',None)
        if not start_date or not end_date:
            return Response({"error":"You Must Provided a start_date o end_date"}, status=status.HTTP_400_BAD_REQUEST)
        
        recordings = service.zoom_api_get_requests(f"https/https://api.zoom.us/v2/users/me/recordings?from={start_date}&to={end_date}")
        
        if recordings[1] == 3:
            #retornamos las grabaciones obtenidas
            return Response({"recordings":recordings[0]},status=status.HTTP_202_ACCEPTED)
        elif recordings[0] == 4:
            recordings = service.zoom_api_get_requests(f"https/https://api.zoom.us/v2/users/me/recordings?from={start_date}&to={end_date}")
        #Si por casualidad al hacer la solicitud de obtener las grabaciones las credenciales son invalidas y se renuevan
        #hariamos otra vez la solicitud
        else:
            return Response({"error":"Ocurrio un error en el servidor al intentar realizar acciones la solicitud"},status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self,request,format=None):
        start_date,end_date = request.query_params.get('start_date',None),request.query_params.get('end_date',None)
        if not start_date or not end_date:
            return Response({"error":"You Must Provided a start_date o end_date"}, status=status.HTTP_400_BAD_REQUEST)
        
         
        service.download_zoom_recordings(start_date,end_date)
        
        #decimos que la solicitud se proceso, pero internamente el proceso va a demorar su tiempo para ejecutarse
        return Response(status=status.HTTP_202_ACCEPTED)