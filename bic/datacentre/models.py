from django.contrib.gis.db import models

########################################
############### KML/GPX ################
########################################

# Fichero KML fuente
class KML_file(models.Model):
    kml_name = models.TextField(help_text="The raw kml file name")
    kml_file = models.FileField(
        verbose_name=("KML File"),
        upload_to='uploads/kml/',
        #storage=OverwriteFileSystemStorage(create_backups=True),
        max_length=511,
        null=True,
        blank=True,
    )
    def __str__(self):
        return self.gpx_name

# Fichero GPX fuente
# desde https://github.com/jedie/django-for-runners/blob/master/src/for_runners/models/gpx.py
class GPX_file(models.Model):
    gpx_name = models.TextField(help_text="The raw gpx file name")
    gpx_file = models.FileField(
        verbose_name=("GPX File"),
        upload_to='uploads/gpx/',
        #storage=OverwriteFileSystemStorage(create_backups=True),
        max_length=511,
        null=True,
        blank=True,
    )
    def __str__(self):
        return self.gpx_name


########################################
############## SENSORS #################
########################################

class SCK_device(models.Model):
    sck_id = models.IntegerField(primary_key=True) # ID provided by SCPlatform
    name = models.CharField(max_length=50, null=True)
    # TODO cómo meter tracks de dispositivo -> Track u otro modelo    
    def __str__(self):
        return self.name

# Modelo que recoge los sensores de SCK + los que queramos meter en un futuro
# Hay que proveer un ID diferente al que da SCK para sensores nuevos    
class Sensor(models.Model):    
    sensor_id = models.IntegerField(primary_key=True) # ID provided by SCPlatform
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=140)
    units = models.CharField(max_length=50, null=True)

    def __str__(self):
        return self.name

########################################
############### Tracks #################
########################################

# Colección de <trkpt>
class Track(models.Model):
    # Django fields corresponding to 
    # layer [tracks] of gpx
    name = models.CharField(max_length=50, null=True)
    start_time = models.DateTimeField(null=True)
    end_time = models.DateTimeField(null=True) 
    distance = models.FloatField(null=True)
    device = models.ForeignKey(SCK_device, on_delete=models.CASCADE, null=True)

    # GeoDjango-field <-> (MultiLineString or LineString) 
    mlstring = models.MultiLineStringField(null=True)
    lstring = models.LineStringField(null=True)

    # Returns the string representation of the model.
    def __str__(self):
        return self.name

# Componentes LineString del KML
class BikeLane(models.Model):
    # Django fields corresponding to 
    # layer [3D LineString] of kml
    name = models.CharField(max_length=50, null=True)
    distance = models.FloatField(null=True)
    #time = models.DateTimeField()

    # GeoDjango-field <-> (MultiLineString or LineString) + Polygon (for buffered bidegorri)
    mlstring = models.MultiLineStringField(null=True)
    lstring = models.LineStringField(null=True)
    poly = models.PolygonField(null=True)

    # Returns the string representation of the model.
    def __str__(self):
        return self.name


# Points dentro de un track: <trkpt>
class Trackpoint(models.Model):
    track = models.ForeignKey(Track, on_delete=models.CASCADE)
    time = models.DateTimeField(null=True) 
    # GeoDjango-field <-> (Point)
    point = models.PointField()

    # Returns the string representation of the model.
    def __str__(self):
        return self.name

# Dtours Tracks-Bidegorris
class Dtour(models.Model):
    track = models.ForeignKey(Track, on_delete=models.CASCADE, null=True)
    distance = models.FloatField(null=True)
    ratio = models.FloatField(null=True)

    # GeoDjango-field <-> (MultiLineString)
    mlstring = models.MultiLineStringField()

########################################
############### Others #################
########################################


class Measurement(models.Model):
    sensor = models.ForeignKey(Sensor, on_delete=models.CASCADE)
    device = models.ForeignKey(SCK_device, on_delete=models.CASCADE)
    trkpoint = models.ForeignKey(Trackpoint, on_delete=models.CASCADE, null=True)
    time  = models.DateTimeField(null=True)
    value = models.FloatField(null=True)
    point = models.PointField()
    
    def __str__(self):
        return self.units

# Configuración de la página
class Config(models.Model):
    name = models.CharField(max_length=50, null=True)
    lon = models.FloatField()

    lat = models.FloatField()
    zoom = models.FloatField()
    devices = models.ManyToManyField(SCK_device)

    def __str__(self):
        return self.name
    