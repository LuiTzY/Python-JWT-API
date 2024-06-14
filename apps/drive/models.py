from django.db import models
from apps.clients.models import Mentor


class Drive(models.Model):
    mentor = models.ForeignKey(Mentor, on_delete=models.CASCADE)
    access_token = models.TextField(null=False)
    refresh_token = models.TextField(null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    

    @classmethod
    def get_drive_credentials_by_mentor(cls,mentor):
        if not mentor:
            return None
        try:
            return cls.objects.get(mentor=mentor)
        except cls.DoesNotExist:
            return None
    
       

class UserDriveEmail(models.Model):
    #Instancia del usuario
    mentor = models.ForeignKey(Mentor,on_delete=models.CASCADE)
    #Correo relacionado a la cuenta de drive
    email = models.EmailField(unique=True)
    
    @classmethod
    def get_email_drive_by_mentor(cls,mentor):
        if not mentor:
            return None
        try:
            cls.objects.get(mentor=mentor)
        
        except cls.DoesNotExist:
            return None