import datetime
from django.utils import timezone
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

# Formulario para Consulta de tracks
class DateTimeRangeBBoxForm(forms.Form):
    since_datetime = forms.DateTimeField(help_text=_("Desde cuándo"))
    until_datetime = forms.DateTimeField(help_text=_("Hasta cuándo"))
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
                raise ValidationError(_('Fecha inválida - rango temporal en tiempo futuro'))
                
        dates = [date1, date2]
        return dates