from django.contrib.gis import admin
from django.contrib.gis.admin import OSMGeoAdmin
from .models import GPX_file, GPX_track, KML_lstring, KML_file, SCK_device, Measurement, Config, Dtour

@admin.register(GPX_track)
class GPXtrackAdmin(OSMGeoAdmin):
    list_display = ('name', 'mlstring')

@admin.register(KML_lstring)
class KMLlstringAdmin(OSMGeoAdmin):
    list_display = ('name', 'lstring')

admin.site.register(GPX_file)
admin.site.register(KML_file)
admin.site.register(SCK_device)
admin.site.register(Measurement)
admin.site.register(Config)
admin.site.register(Dtour)