from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from apps.clients.models import Mentor
from .serializers import UserDriveEmailSerializer, DriveSerializer
from .models import Drive,UserDriveEmail
from .services import DriveAuthService,DriveService
import asyncio

class DriveAuthView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def get(self,request,format=None):
        
        # se obtendra informacion de acerca de la cuenta del usuario
        mentor = Mentor.get_mentor(request.user)
        if mentor == None:
            return Response({"message":"you must be a member to have this funcionality"})
        
        drive = DriveService(mentor,"https://www.googleapis.com/drive/v2/about")
        
        files = asyncio.run(drive.handle_async_req(drive.endpoint))     

        if 'response' in files:
            print("Se encontraron los archivos")
            return Response({'response':files['response']},status=status.HTTP_200_OK)

        return Response({"message":"This endpoint workss","drive":files},status=status.HTTP_200_OK)
    
    def post(self,request,format=None):
        
        auth_code = request.data.get("auth_code",None)
        
        if auth_code == None:
            return Response({"message":"Auth Code is missing"},status=status.HTTP_400_BAD_REQUEST)
        
        mentor = Mentor.get_mentor(request.user)
        
        if mentor == None:
            return Response({"message":"You must be a mentor to have this funcionality"},status=status.HTTP_400_BAD_REQUEST)
        
        mentor_drive = Drive.get_drive_credentials_by_mentor(mentor)
        
        if not mentor_drive == None:
            return Response({"You already are authenticated with your drive account"},status=status.HTTP_400_BAD_REQUEST)
        
        # drive_email_verify = UserDriveEmail.get_email_drive_by_mentor(mentor)
        
        # if drive_email_verify == None:
        #     return Response({"message":"you must have associated email to use this"},status=status.HTTP_400_BAD_REQUEST)
        
        drive = DriveAuthService(auth_code,mentor)
        files = asyncio.run(drive.drive_service())
        print(f"LO que llego de la respuesa de drive {files} \n")
        if files == None:
            return Response({"error":f"Ocurrio un error al intentar autorizar {files}"},status=status.HTTP_400_BAD_REQUEST)
        
        
        drive_data = {
            "mentor":mentor.id,
            "access_token":files['credentials']['access_token'],
            "refresh_token":files['credentials']['refresh_token']

        }
        drive_serializer = DriveSerializer(data=drive_data)
        
        if drive_serializer.is_valid():
            drive_serializer.save()
            return Response({"message":"You authenticated correctly your drive account"},status=status.HTTP_200_OK)
         
        return Response({"error":drive_serializer.errors},status=status.HTTP_400_BAD_REQUEST)


class DriveAccountView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def post(self,request,format=None):
        
        mentor = Mentor.get_mentor(request.user)
        if mentor == None:    
            return Response({"message":"you must be a mentor to have this funcionality"},status=status.HTTP_400_BAD_REQUEST)
    
        email = request.data.get("email",None)
        if email == None:
            return Response({"message":"Miss email"},status=status.HTTP_400_BAD_REQUEST)
        
        serializer_data = {
            "mentor":mentor.id,
            "email":email
        }
        
        drive_email_serializer = UserDriveEmailSerializer(data=serializer_data)
        if drive_email_serializer.is_valid():
            
            drive_email_serializer.save()
            
            return Response({"message":"Saved your drive email account"},status=status.HTTP_201_CREATED)
        
        return Response({"error":drive_email_serializer.errors},status=status.HTTP_400_BAD_REQUEST)