from django.db import models
from apps.users.models import User 
from django.db import models, IntegrityError, transaction



class Mentor(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField(unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"Mentor: {self.name}"
    
    @classmethod
    def get_mentor(cls,mentor):
        if not mentor:
            #si no se proporciona una instancia de un usuario retornamos none
            return None
        try:
            #verficamos si existe y si existe se retorna la instancia encontrada
            return cls.objects.get(user=mentor)
        except cls.DoesNotExist:
            print("No existe")
            #retornamos none
            return None

class Client(models.Model):
    name = models.CharField(max_length=120,null=False)
    email = models.EmailField(unique=True,null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    #persona a la que pertenece el cliente
    mentor = models.ForeignKey(Mentor, on_delete=models.CASCADE)
    
   
    def __str__(self):   
       return f"{self.name} - {self.email}"
    
    @classmethod
    def get_client(cls,email):
        if not email:
            return None
        try:
            return  cls.objects.get(email=email)
        except cls.DoesNotExist:
            return None