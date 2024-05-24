from rest_framework import serializers
from .models import Zoom

class ZoomCredentialsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Zoom
        fields = ("access_token","refresh_token","user")

class ZoomUpdateCredentialsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Zoom
        fields = ("acces_token","refresh_token")

class ZoomDateRecordingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Zoom