from django.contrib.gis import admin
from .models import WorldBorder, GPX_file, KML_file

admin.site.register(WorldBorder, admin.GeoModelAdmin)
admin.site.register(GPX_file)
admin.site.register(KML_file)