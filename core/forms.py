from django import forms
from django.core.exceptions import ValidationError
from datetime import date

class CalculoForm(forms.Form):
    OPCIONES_INDICE = [
        ('costo_construccion', 'Costo de Construcción'),
        ('materiales', 'Materiales'),
        ('mano_obra', 'Mano de Obra'),
    ]

    nombre_proyecto = forms.CharField(
        label="Nombre del Archivo / Proyecto",
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'Ej: Casa Emilio - Certificado 1'})
    )

    fecha_base = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'month', 'class': 'form-control'}),
        label="Fecha Base",
        input_formats=['%Y-%m']
    )
    fecha_final = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'month', 'class': 'form-control'}),
        label="Fecha Final",
        input_formats=['%Y-%m']
    )
    presupuesto = forms.DecimalField(
        min_value=0.01, 
        decimal_places=2, 
        label="Presupuesto Original ($)"
    )
    tipo_indice = forms.ChoiceField(choices=OPCIONES_INDICE, label="Índice de Ajuste")

    def clean(self):
        cleaned_data = super().clean()
        f_base = cleaned_data.get("fecha_base")
        f_final = cleaned_data.get("fecha_final")

        # Definimos el límite histórico de nuestros datos
        fecha_minima = date(2011, 1, 1)

        if f_base and f_final:
            # 1. Validar que no sean anteriores a 2011
            if f_base < fecha_minima:
                self.add_error('fecha_base', "Los registros del índice CAC comienzan en enero de 2011.")
            
            if f_final < fecha_minima:
                self.add_error('fecha_final', "Los registros del índice CAC comienzan en enero de 2011.")

            # 2. Validar orden lógico
            if f_base > f_final:
                raise ValidationError("La fecha base no puede ser mayor a la fecha final.")
            
            # 3. Validar que no pidan meses en el futuro
            hoy = date.today()
            primer_dia_mes_actual = date(hoy.year, hoy.month, 1)
            
            if f_final > primer_dia_mes_actual:
                self.add_error('fecha_final', "No tenemos datos futuros. Selecciona hasta el mes actual.")
        
        return cleaned_data