from django.shortcuts import render
from django.http import HttpResponse
from .forms import CalculoForm
from .utils import generar_excel_mayores_costos

def index(request):
    if request.method == 'POST':
        form = CalculoForm(request.POST)
        if form.is_valid():
            # Extraer datos
            nombre_proy = form.cleaned_data['nombre_proyecto']
            f_base = form.cleaned_data['fecha_base']
            f_final = form.cleaned_data['fecha_final']
            presupuesto = form.cleaned_data['presupuesto']
            tipo_indice = form.cleaned_data['tipo_indice']
            
            # Generar el Excel (Usando el simulador incluido)
            try:
                excel_file = generar_excel_mayores_costos(f_base, f_final, presupuesto, tipo_indice)
                
                if excel_file:
                    response = HttpResponse(
                        excel_file,
                        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    )
                    # Limpiamos el nombre para que no rompa el header HTTP
                    nombre_limpio = nombre_proy.replace(" ", "_").replace(",", "")
                    filename = f"{nombre_limpio}_MayoresCostos.xlsx"
                    
                    response['Content-Disposition'] = f'attachment; filename="{filename}"'
                    return response
                else:
                    form.add_error(None, "Rango de fechas sin datos disponibles en la simulación.")
            
            except Exception as e:
                # Mostrar el error en la pantalla si algo falla en el Excel
                form.add_error(None, f"Error generando Excel: {str(e)}")
                
    else:
        form = CalculoForm()

    return render(request, 'core/index.html', {'form': form})