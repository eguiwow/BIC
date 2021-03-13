import datetime
from django.utils import timezone
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

# Formulario para Consulta de tracks
class DateTimeRangeForm(forms.Form):
    since_datetime = forms.DateTimeField(help_text=_("Desde cuándo"))
    until_datetime = forms.DateTimeField(help_text=_("Hasta cuándo"))

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