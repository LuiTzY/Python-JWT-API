from django.db import models
from apps.users.models import User

class Zoom(models.Model):
    access_token = models.TextField(null=False)
    refresh_token = models.TextField(null=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class UserZoomEmail(models.Model):
    #Instancia del usuario
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    #Correo relacionado a la cuenta de zoom
    email = models.EmailField(unique=True)
    

"""
    La idea aqui es que un usuario relacion un correo electronico con el de su cuenta de zoom(deberan de ser el mismo),
    una vez se haga esto, cuando se ejecute el flujo de autorizacion, se hara una solicitud a la api de zoom para obtener,
    informacion del usuario, si los correos conciden las credenciales se van a guardar, si no coinciden pues se le dira.
"""