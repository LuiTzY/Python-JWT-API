from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view

from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import User
from .serializers import UserSerializer,UserUpdateSerializer,UserUpdatePasswordSerializer
from django.contrib.auth.hashers import make_password

#api view para funciones especificas
#viewsets para crud y funciones por asi decirlo menos especificas

"""
    Las clases basadas en vistas que tenga como autenticacion JWT, si el token es valido automaticamente
    se podra acceder al usuario en el request.user, si no lo es pues no se podra acceder, si el token es 
    invalido, automaticamenet se encargara de enviar la respuesta con los detalles y su estado, tambien
    se encargara de revisar si el usuario relacionado al token existe
"""

#is valid solo se utiliza en los serializadores cuando solo se necesita validar data



class UserDetailView(APIView):
    
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def get(self,request,format=None):
            #Se serializan los datos para que se conviertan en si en json y se muestre en la respuesta, no es neceserio pasarle data, ya que esto seria solo para validacion
            #y no es necesario esto, ya que estamos obteniendo un recurso que anteriormente fue ya validado
            userSerialized = UserSerializer(request.user)
            return Response({"user":userSerialized.data}, status=status.HTTP_202_ACCEPTED)
            #return Response({"error":userSerialized.errors} ,status=status.HTTP_400_BAD_REQUEST)
        
    def put(self, request, format=None):
            #Especificamos el usuario, le pasamos los datos que nos lleguen por post en el request.data y como no sabemos cuantos campos seran actualizados y cuales, establecemos partial en True
            userSerialized = UserUpdateSerializer(request.user,data=request.data, partial=True)
            
            if userSerialized.is_valid():
                userSerialized.save()
                return Response({"user":userSerialized.data}, status=status.HTTP_202_ACCEPTED)
        
            return Response({"error":"No existe un usuario con este id"} ,status=status.HTTP_404_NOT_FOUND)
        
    #Esta ruta sera para actualizar la password del usuario
    def patch(self,request,format=None):
            #le pasamos los datos al serializador para verificar su validez
            passwordSerializer = UserUpdatePasswordSerializer(data=request.data)
            if passwordSerializer.is_valid():         
                #Obtenemos una instancia del usuario para asi poder interactuar con sus metodos
                user = User.objects.get(id=request.user.id)
                #le guardamos las password hashead con el algoritmo de django make_password
                user.password = make_password(request.data['password'])
                #guardamos esa instancia del usuario y no la del serializador
                user.save()   
                return Response({"message":"Password Updated Succesfully"},status=status.HTTP_202_ACCEPTED)
            #Hubo un error al intentar actualizar la password
            return Response({"error":passwordSerializer.errors},status=status.HTTP_400_BAD_REQUEST)


#vista para crear un usuario ojo: Tambien se podria utilizar una clase basada en una vista
@api_view (["POST"])
def singup(request):
    
    #Primer paso serializar los datos que me llegan en la soliciutd
    serializer = UserSerializer(data=request.data)
    
    #Si es valido guardo mi usuario
    if serializer.is_valid():
        user = serializer.save()
        
        token = RefreshToken.for_user(user)
        
        return Response({"user":serializer.data, "token":str(token) }, status=status.HTTP_201_CREATED)
    
    return Response({"error":serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

#Las vista de inicio y cierre de sesion estan explicadas en el archivo de urls de esta app