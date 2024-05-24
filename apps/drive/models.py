from django.db import models
from users.models import User
# Create your models here.
class UserDriveEmail(models.Model):
    #Instancia del usuario
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    #Correo relacionado a la cuenta de drive
    email = models.EmailField(unique=True)