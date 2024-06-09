from rest_framework import serializers
from .models import Zoom

class ZoomCredentialsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Zoom
        fields = ("access_token","refresh_token","mentor")


class ZoomDateRecordingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Zoom