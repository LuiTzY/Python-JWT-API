from django.db import models
from apps.clients.models import Mentor

class Zoom(models.Model):
    access_token = models.TextField(null=False)
    refresh_token = models.TextField(null=False)
    mentor = models.ForeignKey(Mentor, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @classmethod
    def get_zoom_credentials_by_mentor(cls,mentor):
        if not mentor:
            return None
        try:
                return cls.objects.get(mentor=mentor)
        except cls.DoesNotExist:
            return None
    
    #Metodo para eliminar una instancia que nos pasen de un mentor
    @classmethod
    def delete_instance_by_mentor(cls, mentor):
        instance = cls.get_zoom_credentials_by_mentor(mentor)
        if instance:
            instance.delete()
            return True
        return False

class UserZoomEmail(models.Model):
    #Instancia del usuario
    mentor = models.ForeignKey(Mentor, on_delete=models.CASCADE)
    #Correo relacionado a la cuenta de zoom
    email = models.EmailField(unique=True)

    @classmethod
    def get_user_zoom_email(cls,mentor):
        if not mentor:
            return None
        try:
            return cls.objects.get(mentor=mentor)
        except cls.DoesNotExist:
            return None
    
        



"""
    La idea aqui es que un usuario relacion un correo electronico con el de su cuenta de zoom(deberan de ser el mismo),
    una vez se haga esto, cuando se ejecute el flujo de autorizacion, se hara una solicitud a la api de zoom para obtener,
    informacion del usuario, si los correos conciden las credenciales se van a guardar, si no coinciden pues se le dira.
"""