from django.db import models
from apps.clients.models import Mentor

class EmaiTemplate(models.Model):
    template_title = models.CharField(max_length=142,null=False,verbose_name="Titulo de la plantilla")
    email_template = models.TextField(null=False,verbose_name="Plantilla")
    mentor = models.ForeignKey(Mentor,on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True,verbose_name="Creada el")
    update_at = models.DateTimeField(auto_now=True,verbose_name="Actualizado el")
    
    def __str__(self):
        return f"{self.mentor.name} - {self.template_title}"