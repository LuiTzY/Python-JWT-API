from .models import Client
from django.db import IntegrityError


def create_clients(clients):
    
    for client in clients:
        try:
            Client.objects.create(name=client['nombre'],email=client['email'],mentor=client['mentor'])
        except IntegrityError:
            print("Este cliente ya existe \n")
        
    