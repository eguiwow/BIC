import datetime
from django.utils import timezone
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from .models import Config

class DateInput(forms.DateTimeInput):
    # Esta línea comentada hace que salga en formato HTML5 pero sin valor por defecto!
    input_type = 'datetime-local'

# Formulario para Consulta de tracks
class DateTimeRangeBBoxForm(forms.Form):
    since_datetime = forms.DateTimeField(widget=DateInput, help_text=_("Desde cuándo"))
    until_datetime = forms.DateTimeField(widget=DateInput, help_text=_("Hasta cuándo"))
    # DecimalField - https://docs.djangoproject.com/en/3.1/ref/models/fields/ 
    SW_lon = forms.DecimalField(help_text=_("Punto esquina inferior izquierda"))
    SW_lat = forms.DecimalField(help_text=_("Punto esquina inferior derecha"))
    NE_lon = forms.DecimalField(help_text=_("Punto esquina superior izquierda"))
    NE_lat = forms.DecimalField(help_text=_("Punto esquina superior derecha"))

    def clean_range_datetime(self):
        date1 = self.cleaned_data['since_datetime']
        date2 = self.cleaned_data['until_datetime']
        
        # Check if date1 is before date2
        if date1 > date2:
            raise ValidationError(_('Fecha inválida - la primera fecha es mayor que la segunda'))
        else:
            # Check if date2 is not in the future.
            if date2 > timezone.now():
                print(date2)
                print(timezone.now())
                raise ValidationError(_('Fecha inválida - rango temporal en tiempo futuro'))
                
        dates = [date1, date2]
        return dates

# Formulario para Consulta de tracks
class ConfigForm(forms.Form):
    center_lon = forms.DecimalField(help_text=_("Centro del mapa (Longitud [-180 a 180])"))
    center_lat = forms.DecimalField(help_text=_("Centro del mapa (Latitud)[-90 a 90]"))
    center_zoom = forms.IntegerField(help_text=_("Centro del mapa (Zoom)"))

    def clean_range_center(self):
        lon = self.cleaned_data['center_lon']
        lat = self.cleaned_data['center_lat']
        zoom = self.cleaned_data['center_zoom']
        print(lon)
        print(lat)
        # TODO peta no sé por qué al hacer la comprobación
        # Check lon between 180 & -180; lat between 90 & -90; zoom between 0 & 20
        # if lon > 180 or lon < -180:
        #     raise ValidationError(_('Longitud inválida - Tiene que estar entre -180º y 180º'))
        # if lat > 90 or lat < -90:
        #     raise ValidationError(_('Longitud inválida - Tiene que estar entre -180º y 180º'))
        # if zoom > 20 or lon < 0:
        #     raise ValidationError(_('Longitud inválida - Tiene que estar entre -180º y 180º'))

        center = [lon, lat, zoom]
        return center


class ConfigDevicesForm(forms.Form):
    device_id = forms.IntegerField()
    def clean_add_id(self, kit_ids):
        new_id = self.cleaned_data['device_id']
        if new_id in kit_ids:
            raise ValidationError(_('ID ya en uso'))
        return new_id

    def clean_delete_id(self, kit_ids):
        delete_id = self.cleaned_data['device_id']
        if delete_id not in kit_ids:
            raise ValidationError(_('ID no registrado'))
        return delete_id