
# https://medium.com/swlh/build-your-first-rest-api-with-django-rest-framework-e394e39a482c 

from rest_framework import serializers
from .models import Track, BikeLane, Measurement, Dtour

class TrackSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Track
        fields = ('name', 'mlstring', 'start_time', 'end_time', 'distance')

class BikeLaneSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = BikeLane
        fields = ('name', 'lstring', 'distance')

class MeasurementSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Measurement
        fields = ('value', 'units', 'point', 'time', 'sensor_id', 'device_id')

class DtourSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Dtour
        fields = ('mlstring', 'ratio', 'distance')