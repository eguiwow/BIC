# Generated by Django 3.1.6 on 2021-03-13 17:31

import django.contrib.gis.db.models.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('datacentre', '0003_auto_20210313_1146'),
    ]

    operations = [
        migrations.AddField(
            model_name='kml_lstring',
            name='poly',
            field=django.contrib.gis.db.models.fields.PolygonField(null=True, srid=4326),
        ),
    ]
