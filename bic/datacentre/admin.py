from django.contrib.gis import admin
from .models import GPX_file, KML_file #WorldBorder

# Ejemplo de GeoModelAdmin
# admin.site.register(WorldBorder, admin.GeoModelAdmin)

# Registros propios
admin.site.register(GPX_file)
admin.site.register(KML_file)