from django.contrib.gis import admin
from .models import GPX_file, KML_file, SCK_device

admin.site.register(GPX_file)
admin.site.register(KML_file)
admin.site.register(SCK_device)