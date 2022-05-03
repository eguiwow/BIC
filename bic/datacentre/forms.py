import datetime
from django.utils import timezone
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from .models import Config

import logging
logger = logging.getLogger(__name__)

class DateInput(forms.DateTimeInput):
    input_type = 'datetime-local'

# Formulario para Consulta espaciotemporal de tracks
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
                logger.info(date2)
                logger.info(timezone.now())
                raise ValidationError(_('Fecha inválida - rango temporal en tiempo futuro'))
                
        dates = [date1, date2]
        return dates


# Formulario para Consulta de rangos espaciotemporales de tracks
class MultipleDateTimeRangeForm(forms.Form):
    since_dt1 = forms.DateTimeField(widget=DateInput, help_text=_("Desde cuándo"))
    until_dt1 = forms.DateTimeField(widget=DateInput, help_text=_("Hasta cuándo"))
    since_dt2 = forms.DateTimeField(widget=DateInput,required=False, help_text=_("Desde cuándo"))
    until_dt2 = forms.DateTimeField(widget=DateInput,required=False, help_text=_("Hasta cuándo"))
    since_dt3 = forms.DateTimeField(widget=DateInput,required=False, help_text=_("Desde cuándo"))
    until_dt3 = forms.DateTimeField(widget=DateInput,required=False, help_text=_("Hasta cuándo"))
    since_dt4 = forms.DateTimeField(widget=DateInput,required=False, help_text=_("Desde cuándo"))
    until_dt4 = forms.DateTimeField(widget=DateInput,required=False, help_text=_("Hasta cuándo"))
    since_dt5 = forms.DateTimeField(widget=DateInput,required=False, help_text=_("Desde cuándo"))
    until_dt5 = forms.DateTimeField(widget=DateInput,required=False, help_text=_("Hasta cuándo"))
    # DecimalField - https://docs.djangoproject.com/en/3.1/ref/models/fields/ 
    SW_lon = forms.DecimalField(help_text=_("Punto esquina inferior izquierda"))
    SW_lat = forms.DecimalField(help_text=_("Punto esquina inferior derecha"))
    NE_lon = forms.DecimalField(help_text=_("Punto esquina superior izquierda"))
    NE_lat = forms.DecimalField(help_text=_("Punto esquina superior derecha"))

    def clean_range_datetime(self):
        s_dt1 = self.cleaned_data['since_dt1']
        u_dt1 = self.cleaned_data['until_dt1']
        s_dt2 = self.cleaned_data['since_dt2']
        u_dt2 = self.cleaned_data['until_dt2']
        s_dt3 = self.cleaned_data['since_dt3']
        u_dt3 = self.cleaned_data['until_dt3']
        s_dt4 = self.cleaned_data['since_dt4']
        u_dt4 = self.cleaned_data['until_dt4']
        s_dt5 = self.cleaned_data['since_dt5']
        u_dt5 = self.cleaned_data['until_dt5']

        # 1 Check if s_dt is before u_dt
        if s_dt1 > u_dt1:
            raise ValidationError(_('Fecha inválida - la primera fecha es mayor que la segunda'))
        else:
            # Check if u_dt is not in the future.
            if u_dt1 > timezone.now():
                logger.info(u_dt1)
                logger.info(timezone.now())
                raise ValidationError(_('Fecha inválida - rango temporal en tiempo futuro'))                
        # 2 Check if s_dt is before u_dt
        if s_dt2:
            if s_dt2 > u_dt2:
                raise ValidationError(_('Fecha inválida - la primera fecha es mayor que la segunda'))
            else:
                # Check if u_dt is not in the future.
                if u_dt2 > timezone.now():
                    logger.info(u_dt2)
                    logger.info(timezone.now())
                    raise ValidationError(_('Fecha inválida - rango temporal en tiempo futuro'))
        # 3 Check if s_dt is before u_dt
        if s_dt3:
            if s_dt3 > u_dt3:
                raise ValidationError(_('Fecha inválida - la primera fecha es mayor que la segunda'))
            else:
                # Check if u_dt is not in the future.
                if u_dt3 > timezone.now():
                    logger.info(u_dt3)
                    logger.info(timezone.now())
                    raise ValidationError(_('Fecha inválida - rango temporal en tiempo futuro'))                
        # 4 Check if s_dt is before u_dt
        if s_dt4:        
            if s_dt4 > u_dt4:
                raise ValidationError(_('Fecha inválida - la primera fecha es mayor que la segunda'))
            else:
                # Check if u_dt is not in the future.
                if u_dt4 > timezone.now():
                    logger.info(u_dt4)
                    logger.info(timezone.now())
                    raise ValidationError(_('Fecha inválida - rango temporal en tiempo futuro'))
        # 5 Check if s_dt is before u_dt
        if s_dt5:
            if s_dt5 > u_dt5:
                raise ValidationError(_('Fecha inválida - la primera fecha es mayor que la segunda'))
            else:
                # Check if u_dt is not in the future.
                if u_dt5 > timezone.now():
                    logger.info(u_dt5)
                    logger.info(timezone.now())
                    raise ValidationError(_('Fecha inválida - rango temporal en tiempo futuro'))

        dates = [[s_dt1, u_dt1], [s_dt2, u_dt2], [s_dt3, u_dt3], [s_dt4, u_dt4], [s_dt5, u_dt5]]
        return dates



# Formulario para cambio de centro mapa
class ConfigForm(forms.Form):
    center_lon = forms.DecimalField(help_text=_("Centro del mapa (Longitud [-180 a 180])"))
    center_lat = forms.DecimalField(help_text=_("Centro del mapa (Latitud)[-90 a 90]"))
    center_zoom = forms.IntegerField(help_text=_("Centro del mapa (Zoom)"))

    def clean_range_center(self):
        lon = self.cleaned_data['center_lon']
        lat = self.cleaned_data['center_lat']
        zoom = self.cleaned_data['center_zoom']
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

# Formulario para editar lista de dispositivos
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

# Formulario para editar lista de fechas
class ConfigDatesForm(forms.Form):
    since_datetime = forms.DateTimeField(widget=DateInput, help_text=_("Desde cuándo"))
    until_datetime = forms.DateTimeField(widget=DateInput, help_text=_("Hasta cuándo"))

    def clean_range_datetime(self):
        date1 = self.cleaned_data['since_datetime']
        date2 = self.cleaned_data['until_datetime']
        
        # Check if date1 is before date2
        if date1 > date2:
            raise ValidationError(_('Fecha inválida - la primera fecha es mayor que la segunda'))
        else:
            # Check if date2 is not in the future.
            if date2 > timezone.now():
                logger.info(date2)
                logger.info(timezone.now())
                raise ValidationError(_('Fecha inválida - rango temporal en tiempo futuro'))
                
        dates = [date1, date2]
        return dates
    
    def clean_add_id(self, kit_ids):
        new_since = self.cleaned_data['since_datetime']
        new_until = self.cleaned_data['until_datetime']
        # if new_id in kit_ids:
        #     raise ValidationError(_('ID ya en uso'))
        return new_since

    # def clean_delete_id(self, kit_ids):
    #     delete_id = self.cleaned_data['device_id']
    #     if delete_id not in kit_ids:
    #         raise ValidationError(_('ID no registrado'))
    #     return delete_id

# Formulario para subir archivos GPX
class UploadGPXForm(forms.Form):
    file = forms.FileField()