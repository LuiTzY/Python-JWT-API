from rest_framework import serializers
from .models import User
from rest_framework_simplejwt.views import  TokenObtainPairView

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

"""
    Tener en cuenta que para cada serializador podemos tener un queryset, para que saque los resultados
"""
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['email'] = user.email
        

        return token
    
class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer
    
    
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("first_name","last_name","email","created_at")

class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

class UserUpdatePasswordSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("password",)
        