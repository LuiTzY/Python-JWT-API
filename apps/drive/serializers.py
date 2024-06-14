from rest_framework import serializers
from .models import Drive,UserDriveEmail


class DriveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Drive
        fields = ("mentor","access_token","refresh_token")
        

class UserDriveEmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDriveEmail
        fields = ("email","mentor")