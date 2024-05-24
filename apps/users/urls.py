from django.urls import path
from . import views,serializers
from rest_framework_simplejwt.views import TokenRefreshView 
from rest_framework_simplejwt.views import TokenBlacklistView

#Nota: La vista para el inicio de sesion sera la del token, ya que pasaremos los datos y obtendremos los tokens para la sesion
urlpatterns = [
    path("singup/", views.singup, name="singup" ),
    path('user/', views.UserDetailView.as_view(), name="user"),
    path('token/', serializers.MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/blacklist/', TokenBlacklistView.as_view(), name='token_blacklist'), #Vista para invalidar un token
]

"""
    El cierre de sesion se hara borrando el token de la sesion del localstorage, luego asi eliminando el token de refresh para esa sesion de igual manera
    haciendo la solicitud a token/blacklist, tener en cuenta que cuando refrescquemos el token, para obtener un nuevo access token este va a ser blacklisteado
    tambien
"""