from .models import Calendly
from rest_framework import serializers


class CalendlySerializer(serializers.ModelSerializer):
    class Meta:
        model = Calendly
        fields = ('calendly_token','mentor')
        


