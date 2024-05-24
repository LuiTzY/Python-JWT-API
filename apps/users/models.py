from django.db import models
from django.contrib.auth.models import BaseUserManager,AbstractBaseUser
from simple_history.models import HistoricalRecords

class UserManager(BaseUserManager):
      
    
     def create_user(self,first_name, last_name,email,password= None):
        if not email:
            raise ValueError("El usuario debe de tener un correo electronico")
        #Cuando hago referencia a self.model la hago a mi clase User que creo yo
        user = self.model(
            email = self.normalize_email(email),
            first_name = first_name,
            last_name = last_name
        )
        #No es necesario colocarlo en la instancia ya que el meto set_password lo hara
        #ademas de encriptar la password que le pase
        user.set_password(password)
        #se guarda el usuario que se creo
        user.save()
        return user
    
     def create_superuser(self, first_name, last_name, email, password):
        user = self.create_user(
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password
        )
        user.is_staff = True  # Establecer is_staff en True
        user.is_superuser = True  # Establecer is_superuser en True
        user.save(using=self._db)
        return user

    
class User(AbstractBaseUser):
    first_name = models.CharField(max_length=50, verbose_name="Nombre")
    last_name = models.CharField(max_length=50, verbose_name="Apellido")
    email = models.EmailField(unique=True, max_length=200, verbose_name="Correo Electronico")
    password = models.CharField(max_length=128, verbose_name="Contraseña")
    user_active = models.BooleanField(default=True,verbose_name="Usuario Activo")
    user_admin = models.BooleanField(default=False, verbose_name="Usuario administrador")
    created_at = models.DateField(auto_now_add = True, verbose_name = "Creado el")
    update_at = models.DateField(auto_now=True, verbose_name = "Actualizado el")
    historial = HistoricalRecords()
    
    objects = UserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('first_name','last_name')
    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
    
     #La forma que se va a imprimir el objeto de tipo usuario
    def __str__(self):
        return f"{self.email} - {self.first_name}"
    
    def has_perm(self,perm,obj=None):
        return True
    
    def has_module_perms(self,app_label):
        return True
    
   
    @property
    def is_staff(self):
        return self.user_admin
    
    @is_staff.setter
    def is_staff(self, value):
        self.user_admin = value
        

