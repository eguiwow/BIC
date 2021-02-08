from django.contrib.gis.db import models

# Create your models here.
class WorldBorder(models.Model):
    name = models.CharField(max_length=50)
    area = models.IntegerField()
    pop2005 = models.IntegerField('Population 2005')
    fips = models.CharField('FIPS Code', max_length=2, null=True)
    iso2 = models.CharField('2 Digit ISO', max_length=2)
    iso3 = models.CharField('3 Digit ISO', max_length=3)
    un = models.IntegerField('United Nations Code')
    region = models.IntegerField('Region Code')
    subregion = models.IntegerField('Sub-Region Code')
    lon = models.FloatField()
    lat = models.FloatField()

    # GeoDjango-specific: a geometry field (MultiPolygonField)
    mpoly = models.MultiPolygonField()

    # Returns the string representation of the model.
    def __str__(self):
        return self.name


class Ruta(models.Model):
    name = models.CharField(max_length=50)
    mp = models.MultiPointField()

    def __str__(self):
        return self.name

class Punto(models.Model):
    p = models.PointField()
    timestamp = models.CharField(max_length=50) #TODO esto debería ser tipo timestamp o algo por el estilo?
    ruta = models.ForeignKey(Ruta, on_delete=models.CASCADE)

# class GPX_info(models.Model):
#     wayPoints = models.PointField()
#     routes = models.LineStringField()
#     tracks = models.MultiLineString()
#     routePoints = models.PointField()
#     trackPoints = models.PointField()

class GPX_file(models.Model): # desde https://github.com/jedie/django-for-runners/blob/master/src/for_runners/models/gpx.py
    gpx_name = models.TextField(help_text="The raw gpx file name")
    gpx_file = models.FileField(
        verbose_name=("GPX Track"),
        upload_to='uploads/gpx/',
        #storage=OverwriteFileSystemStorage(create_backups=True),
        max_length=511,
        null=True,
        blank=True,
    )
    def __str__(self):
        return self.gpx_name

class KML_file(models.Model):
    kml_name = models.TextField(help_text="The raw kml file name")
    kml_file = models.FileField(
        verbose_name=("KML track"),
        upload_to='uploads/kml/',
        max_length=511,
        null=True,
        blank=True,
    )
    def __str__(self):
        return self.kml_name