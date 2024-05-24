import asyncio
from .tasks import start_downloads_sync
from threading import Thread
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

videos = (("https://www.youtube.com/watch?v=YQbgdIvC4Io","D:/Zoom Grabaciones/vid.mp4"),
          ("https://www.youtube.com/watch?v=YQbgdIvC4Io","D:/Zoom Grabaciones/eladio.mp4"),
          ("https://www.youtube.com/watch?v=YQbgdIvC4Io","D:/Zoom Grabaciones/vid2.mp4"))

class ZoomRecordDownloadView(APIView):
    
   def post(self, request, format=None):
        print("Hola")
        thread = Thread(target=start_downloads_sync, args=(videos,))
        thread.start()
        return Response({"message": "Download Started"}, status=status.HTTP_200_OK)
    
   