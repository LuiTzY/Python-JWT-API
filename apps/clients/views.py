from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework.permissions import IsAuthenticated

from rest_framework_simplejwt.authentication import JWTAuthentication

from .serializers import MentorSerializer

#vista para la creacion de un mentor

class MentorView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self,request,format=None):
        pass
    
    def post(self,request,format=None):
        request.data['user'] = request.user.id
        mentor= MentorSerializer(data=request.data)
        if mentor.is_valid():
            mentor.save()
            return Response({"message":"You registered as a mentor perfectly"},status=status.HTTP_200_OK)
        
        return Response({"error":mentor.errors},status=status.HTTP_400_BAD_REQUEST)