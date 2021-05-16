
# https://medium.com/swlh/build-your-first-rest-api-with-django-rest-framework-e394e39a482c 

from rest_framework import serializers
from .models import GPX_track, KML_lstring, Measurement

class GPX_trackSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = GPX_track
        fields = ('name', 'mlstring', 'start_time', 'end_time', 'distance')

class KML_lstringSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = KML_lstring
        fields = ('name', 'lstring', 'distance')

class MeasurementSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Measurement
        fields = ('value', 'units', 'point', 'time', 'sensor_id', 'device_id')