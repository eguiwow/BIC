from django.contrib.gis.db import models

########################################
################ GPX ###################
########################################

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


# Para punto INICIAL y FINAL del track
class GPX_waypoint(models.Model):
    # Django fields corresponding to 
    # layer [waypoints] of gpx
    name = models.CharField(max_length=50, null=True)

    lon = models.FloatField()
    lat = models.FloatField()

    # GeoDjango-field <-> (Point)
    point = models.PointField()

    # Returns the string representation of the model.
    def __str__(self):
        return self.name

# Colección de <trkpt>
class GPX_track(models.Model):
    # Django fields corresponding to 
    # layer [tracks] of gpx
    name = models.CharField(max_length=50, null=True)

    # GeoDjango-field <-> (MultiLineString)
    mlstring = models.MultiLineStringField()

    # Returns the string representation of the model.
    def __str__(self):
        return self.name

# Points dentro de un track: <trkpt>
class GPX_trackpoint(models.Model):
    # Django fields corresponding to 
    # layer [trackpoints] of gpx
    name = models.CharField(max_length=50, null=True)

    track_id = models.ForeignKey(GPX_track, on_delete=models.CASCADE)
    # TODO Decidir si implementar segments 
    # track_seg_id = models.ForeignKey(GPX_seg, on_delete=models.CASCADE)
    lon = models.FloatField()
    lat = models.FloatField()
    ele = models.FloatField()
    time = models.DateTimeField()

    # GeoDjango-field <-> (Point)
    point = models.PointField()

    # Returns the string representation of the model.
    def __str__(self):
        return self.name


########################################
################ KML ###################
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

# Componentes LineString del KML
class KML_lstring(models.Model):
    # Django fields corresponding to 
    # layer [3D LineString] of kml
    name = models.CharField(max_length=50, null=True)

    # GeoDjango-field <-> (LineString)
    lstring = models.LineStringField()

    # Returns the string representation of the model.
    def __str__(self):
        return self.name


########################################
############## GeoJSON #################
########################################
