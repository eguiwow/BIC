from django.contrib.gis import admin
from django.contrib.gis.admin import OSMGeoAdmin
from .models import GPX_file, Track, BikeLane, KML_file, SCK_device, Measurement, Config, Dtour, Sensor

@admin.register(Track)
class TrackAdmin(OSMGeoAdmin):
    list_display = ('name', 'mlstring')

@admin.register(BikeLane)
class BikeLaneAdmin(OSMGeoAdmin):
    list_display = ('name', 'lstring')

admin.site.register(GPX_file)
admin.site.register(KML_file)
admin.site.register(SCK_device)
admin.site.register(Measurement)
admin.site.register(Config)
admin.site.register(Dtour)
admin.site.register(Sensor)