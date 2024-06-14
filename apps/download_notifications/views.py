from threading import Thread
from rest_framework import status
from apps.clients.models import Mentor
from .tasks import start_downloads_sync
from datetime import datetime,timedelta
from rest_framework.views import APIView
from apps.zoom.services import ZoomService 
from apps.zoom.models import Zoom
from apps.calendly.models import Calendly
from rest_framework.response import Response

videos = (("https://www.youtube.com/watch?v=YQbgdIvC4Io","D:/Zoom Grabaciones/vid.mp4"),
          ("https://www.youtube.com/watch?v=YQbgdIvC4Io","D:/Zoom Grabaciones/eladio.mp4"),
          ("https://www.youtube.com/watch?v=YQbgdIvC4Io","D:/Zoom Grabaciones/vid2.mp4"))
"""
   Lo que se hara es crear el hilo desde el servicio de zoom para que desde ahi obtenga todas las urls de descarga,
   tener en cuenta que para descargar las grabaciones no sera el mismo proceso que para obtenerlas, ya que para ob-
   ternerlas debemos de estar autenticados en zoom, puede que llegue a ser necesario en grabaciones que tengan una 
   password mandar el token, por lo que habria que tener en cuenta el renuevo de tokens para ese caso, esto solo
   ocurriria para grabaciones que se hagan la solicitud, hay que tener un trigger o algo para verificar el peso de
   la grabacion de un principio hasta que se suba a drive, esto es xq puede que suba pero no se haya descargado c-
   oorectamete debido a que un token se haya invalidado etc.
"""
service = ZoomService()

#tener en cuenta que el que consuma esta vista es xq quiere hacer la automatizacion completa por lo que debe de tener zoom,calendly,notion y drive autorizados
class ZoomRecordDownloadView(APIView):
   def get (self,request,format=None):
      
      start = request.query_params.get('start_date',None)
      print(start)
      try:
      #convertimos la fecha de inicio en un tipo date time con el formato de year-month-day
        start_date = datetime.strptime(start, "%Y-%m-%d")
      except Exception:
          return Response({"error":"Provided a valid date"},status=status.HTTP_400_BAD_REQUEST)
      
      #calculamos los proximos 7 dias desde la fecha de inicio para que las reuniones de calendly coincidan con las de zoom
      end_date = start_date + timedelta(days=7)
      print(f"Estos son los parametros de las fechas incio{start_date} y fin {end_date}")
      
      #se intentara buscar un mentor relacionado al usuario que este haciendo la peticion
      mentor = Mentor.get_mentor(request.user)
      if mentor is None:
          return Response({"message":"You must be a mentor to have this functionality"},status=status.HTTP_409_CONFLICT)
      
      apps_needed = []
      #Registro de valores retornados por cada app, del mentor recibido, asi sabremos si en una de estas apps el mentor no esta registrado
      
      #credenciales de zoom obtenidas por un mentor
      mentor_credentials = Zoom.get_zoom_credentials_by_mentor(mentor)
      apps_needed.append(["zoom",mentor_credentials])
      calendly_credentials = Calendly.get_calendly_token_by_mentor(mentor)
      apps_needed.append(["calendly",calendly_credentials])
      #aqui faltaria obtener las credenciales de drive,notion y email

      for app in apps_needed:
          if app[1] == None:
              return Response({"message":"You miss this app to automatize your clients records","app_name":app[0]},status=status.HTTP_403_FORBIDDEN)
          
          
          
      
    #   if mentor_credentials == None:
    #       return Response({"message":"To use this you need authorize our zoom app for automatize this"},status=status.HTTP_403_FORBIDDEN)
      
      
      
      #devolvemos las grabaciones encontradas con la cuenta del mentor
      records = service.download_zoom_recordings(start_date,end_date,mentor,calendly_credentials)
      print(records)
      if 'records_found' in records:
          if records['records_found'] == 0:
            return Response({"message":"No records matches with this date"},status=status.HTTP_404_NOT_FOUND)
        
          print("No llega \n")
          #Se crea un hilo para trabajar con las grabaciones de manera asincronica, utilizando la funcionce de start_downloads_async y se le pasan los argumentos de la funcion
          thread = Thread(target=start_downloads_sync, args=(records['records_info'],mentor_credentials.access_token))
          #Iniciamos el hilo
          thread.start()
          
      print(f"Grabaciones encontradas \n")
      
      return Response({"records":records},status=status.HTTP_200_OK)
   
   def post(self, request, format=None):
        print("Se realizo una solicitud para enviar el progreso de descarga para el usuario {}\n".format(request.user.first_name))
        
        #En los parametros esperamos recibir fechas para buscar las grabaciones que coincidan 
        start_date,end_date = request.query_params.get('start_date',None),request.query_params.get('end_date',None)
        
        print(f"Fechas en las que se buscaran las grabaciones {start_date}: {end_date} \n") 
               
        if  start_date == None  or  end_date == None:
            return Response({"error":"You Must Provided a start_date o end_date"}, status=status.HTTP_400_BAD_REQUEST)
        
        recordings = service.zoom_api_get_requests(f"https://api.zoom.us/v2/users/me/recordings?from={start_date}&to={end_date}",request.user)
        
        if recordings[0] == 3:
            #Se crea un hilo para trabajar con las grabaciones de manera asincronica, utilizando la funcionce de start_downloads_async y se le pasan los argumentos de la funcion
            thread = Thread(target=start_downloads_sync, args=(recordings[1],))
            #Iniciamos el hilo
            thread.start()
            #Evniamos un mensaje de que la solicitud se proceso con exito
            return Response({"message": "Download Started"}, status=status.HTTP_200_OK)
        #en el caso de que el token haya expirado, haremos la solicitud nuevamente para obtener las grabaciones
        elif recordings[0] == 4:
            recordings = service.zoom_api_get_requests(f"https://api.zoom.us/v2/users/me/recordings?from={start_date}&to={end_date}",request.user)
            #Se crea un hilo para trabajar con las grabaciones de manera asincronica, utilizando la funcionce de start_downloads_async y se le pasan los argumentos de la funcion
            thread = Thread(target=start_downloads_sync, args=(recordings[1],))
            #Iniciamos el hilo
            thread.start()
            #Evniamos un mensaje de que la solicitud se proceso con exito
            return Response({"message": "Download Started"}, status=status.HTTP_200_OK)
        #Si por casualidad al hacer la solicitud de obtener las grabaciones las credenciales son invalidas y se renuevan
        #hariamos otra vez la solicitud
        else:
            return Response({"error":"Ocurrio un error en el servidor al intentar realizar acciones la solicitud"},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
         
         
        
    
   