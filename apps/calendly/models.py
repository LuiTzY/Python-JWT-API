from django.db import models
from apps.clients.models import Mentor

class Calendly(models.Model):
    mentor = models.ForeignKey(Mentor,on_delete=models.CASCADE)
    calendly_token = models.TextField(null=False) 
    
    @classmethod
    def get_calendly_token_by_mentor(cls,mentor):
        if not mentor:
            return None
        try:
            return cls.objects.get(mentor=mentor)
        except cls.DoesNotExist:
            return None
    def __str__(self):
        return f"Calendly Token for {self.mentor.name}"
    
# #modelo que almacenara el correo de la cuenta de calendly a la que se asocia
# class UserCalendlyEmail(models.Model):
#     email = models.EmailField(unique=True)
#     mentor = models.ForeignKey(Mentor,on_delete=models.CASCADE)

    
#     @classmethod
#     def get_calendly_email_by_mentor(cls,mentor):
#         if not mentor:
#             return None
#         try:
#             return cls.objects.get(mentor=mentor)
#         except cls.DoesNotExist:
#             return None
#     @classmethod
#     def delete_calendly_by_mentor_instance(cls,mentor):
#         instance = cls.get_calendly_email_by_mentor(mentor)
#         if instance:
#             instance.delete()
#             return True
#         return False