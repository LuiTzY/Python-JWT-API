import os
import requests
from dotenv import load_dotenv
from datetime import datetime,timedelta
from apps.errors.views import load_json_error
load_dotenv()

"""
    Para utilizar la api de calendly tenemos 2 maneras, una generando un token personal si son para fines privados
    y la otra es una app oauth si son para fines publicos
"""




#Solo se obtendra los eventos de 7 dias contando desde el dia actual, esto solo para obtener los eventos que nos interesen

#Las fechas que se buscaran seran el mismo rango de fechas que de zoom

class CalendlyService():
    def __init__(self):
        self.headers = {    
        "Content-Type": "application/json",
        'Authorization':'Bearer {}'.format(os.getenv("CalendlyTokenApi"))
        }
        
       
        #aqui se va a guardar una lista de los eventos que sean presenciales
        self.presencial_events_uri = []
        
    
    #Se guardaran en una lista por comprension solo los eventos que no hayan sido cancelados
    def filter_actived_events(self,events):
        #Obtendremos una lista de collection donde cada indice representa un evento programado
        #por lo que iteramos sobre ella obteniendo asi el event y verificando si dentro de este objeto
        #se encuentra el diccionario de cancellation
        return [(event) for event in events['collection'] if not event.get('cancellation') ]
    
    def get_sheduled_events(self,start_date,end_date):
        

        #Retornaremos una lista con (1 y la respuesta) si no hubo errores y se proceso la solicitud
        #Retornaremos una lista con( 0 y el error )si hubieron errores al procesar la solicutd
        print(f"Esta es la fecha de inicio {start_date} y esta es la fecha de fin {end_date} en las que se obtendran los eventos\n")

        try:
            #Endpoint de calendly para obtener los eventos dado un tiempo minimo y maximo de fechas, se obtendran los de los ultimos 7 dias, contando desde que se ejecute el script
            url = f"https://api.calendly.com/scheduled_events?user=https://api.calendly.com/users/DGFGNV3BZMXVXALA&count=100&min_start_time={start_date}&max_start_time={end_date}"
            aurl = "https://api.calendly.com/scheduled_events?user=https://api.calendly.com/users/DGFGNV3BZMXVXALA&count=100&min_start_time=2024-05-09T00:00:00.000000Z&max_start_time=2024-05-10T00:00:00.000000Z"

            #hacemos la solicitud a la url, enviando las cabeceras necesarias incluyendo el token
            scheduled_events = requests.get(url=url,headers=self.headers)
            print(f"URL DE CALENDLY PARA LA SOLICITUD {scheduled_events.url}")
            #convertimos la respuesta en un formato json, para poder acceder a el
            response = scheduled_events.json()
            print(response)
            #al hacer la solicitud, obtendremos 2 objetos, una collection y un paginatio
            #collection es el que contiene el resultado de los eventos, mientras que pagination no es necesario ya que solo brina informacion de tokens de pagina y conteos de resultados
            response.pop("pagination")
            
            #Devolvera una lista de los eventos que no esten cancelados
            actived_events = self.filter_actived_events(response)
            
            #Solo se devolveran los eventos que no esten cancelados y solo sean presenciales
            return [1, actived_events]
        
        #Se captura la excepcion que ocurra al hacer la solicitud
        except requests.exceptions.HTTPError as e:
            error = str(e)
            load_json_error(error)
            print(f"Ocurrio un error con la solicitud al intentar obtener los eventos programados debido a esto: {e} \n")
            return [1,e]
        
    #Hay que tener una lista de los eventos que son presenciales y excluirlos de la solicitud, ya que estos no tendrian un id de reunion de zoom y podra ocasionar errores
    
    #El metodo espera obtener una lista de diccionarios de los eventos
    def get_scheduled_events_invite_email(self,start_date,end_date):
        
        #lista donde se guardaran un diccionario de cada cliente, de los eventos obtenidos
        clients_from_events = []
        """
            Igualmente esta funcion devolvera 2 tipos de lista diferentes segun los resultados
            #0 Si ocurrio un  (0 y el error)
            #1 Si se proceso todo correctamente y no hay errores (1 y la respuesta)
        """        
        #obtenemos los eventos
        actived_events = self.get_sheduled_events(start_date,end_date)
        
        if actived_events[0] == 1:
            #Esto significa que si se proceso la solicitud y tenemos una respuesta
            
            #Al ser una lista donde cada indice es un objeto de un evento, la iteramos para obtener los invitados de ese evento (cliente)
            for event in actived_events[1]:
                """
                
                    Cada vez que obtengamos un evento tendremos el uri de este evento,lo que sucede es que ncesitamos mas detalles de ese evento en especifico
                    como los invitados, para esto necesitamos el uuid de esa uri, lo que sucede es que es una url completa y de esa url la segmentaremos en un lista
                    separados por los slash, donde el ultimo elemento de esa lista sera el uuid (-1)
                """
                uri_uuid = event['uri'].split("/")
                uuid = uri_uuid[-1]
                
                # una vez se crean las carpetas asociadas, con el email del cliente
                #Se hace una solicitud por get para obtener los detalles de los invitados de ese evento, asi se obtendran informaciones como el correo y nombre del cliente
                
                try: 
                    
                    event_guest = requests.get(url=f"https://api.calendly.com/scheduled_events/{uuid}/invitees",headers=self.headers)
                    #Si hay errores en la solictud hacemos que lo retorne para capturarlo con el except
                    event_guest.raise_for_status()
                    
                  
                except requests.exceptions.HTTPError as e:
                    error = str(e)
                    load_json_error(error)
                    print(f"Ocurrio un error al obtener los invitados {e} \n")
                    #se va a retornar como respuesta una lista de todos los eventos con sus clientes, incluyendo el nombre del cliente, email y id de la reunion de zoom
                    #esto para que cuando se vaya a descargar una reunion, de todas estas respuestas con el id de esa reunion identificara a quien pertenece
                    return [0,e]
                
                else:
                    invite = event_guest.json()
                    print(f"""
                    
                    Evento {event['uri']} 
                    Fecha en la que se iniciaria el evento {event['start_time']}
                    Fecha en la que se terminara el evento {event['end_time']}
                    El uri del evento asociado {event['event_type']}
                    El id de la reunion de zoom asociado a este evento {event['location']['data']['id']}
                    Este evento es para: {invite['collection'][0]['name']}
                    Este es el correo de la persona que se le asignara la carpeta en el drive {invite['collection'][0]['email']}
                    \n""")
                
                
                    clients_from_events.append({
                        'nombre':invite['collection'][0]['name'],
                        'email':invite['collection'][0]['email'],
                        'reunion_id':event['location']['data']['id']
                    })
                    return [1,clients_from_events]
                     
        else:
            #Significa que ocurrio un error con la solicitud
            print(f"Ocurrio un error al obtener los eventos programdos {actived_events[1]} \n")
            
            return [0, actived_events[1]]
        

        
