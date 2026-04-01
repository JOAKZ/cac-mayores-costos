import pandas as pd
import io
from .models import IndiceCAC  # Importamos tu nuevo modelo

def obtener_datos_bd():
    """Extrae los datos de SQL y los convierte en un DataFrame limpio."""
    # Extraemos solo las columnas que necesitamos
    queryset = IndiceCAC.objects.all().values(
        'fecha', 'costo_construccion', 'materiales', 'mano_obra'
    )
    
    # Si por alguna razón la BD está vacía, devolvemos un DataFrame vacío
    if not queryset:
        return pd.DataFrame()

    # Convertimos los registros de Django directamente a Pandas
    df = pd.DataFrame.from_records(queryset)
    
    # Ordenamos cronológicamente (por si el modelo no lo hace)
    df = df.sort_values('fecha').reset_index(drop=True)
    
    # Casting de tipos: Aseguramos fechas para comparar y floats para la matemática
    df['fecha'] = pd.to_datetime(df['fecha'])
    df['costo_construccion'] = df['costo_construccion'].astype(float)
    df['materiales'] = df['materiales'].astype(float)
    df['mano_obra'] = df['mano_obra'].astype(float)
    
    return df

def generar_excel_mayores_costos(fecha_base, fecha_final, presupuesto, tipo_indice):
    # 1. Obtener datos reales (ETL desde SQLite)
    df = obtener_datos_bd()
    
    if df.empty:
        return None

    # 2. Filtrar por fechas
    fecha_base = pd.to_datetime(fecha_base).replace(day=1)
    fecha_final = pd.to_datetime(fecha_final).replace(day=1)
    
    mask = (df['fecha'] >= fecha_base) & (df['fecha'] <= fecha_final)
    df_filtrado = df.loc[mask].copy()
    
    if df_filtrado.empty:
        return None

    # 3. Cálculos Matemáticos
    indice_base_valor = df_filtrado.iloc[0][tipo_indice]
    
    df_filtrado['Coeficiente'] = (df_filtrado[tipo_indice] / indice_base_valor) - 1
    df_filtrado['Importe'] = df_filtrado['Coeficiente'] * float(presupuesto)
    
# 4. Formateo para Excel con openpyxl
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_export = pd.DataFrame({
            'Fecha': df_filtrado['fecha'].dt.strftime('%Y-%m'), 
            'Indice': df_filtrado[tipo_indice],
            '% Incidencia': df_filtrado['Coeficiente'],
            'Importe': df_filtrado['Importe']
        })
        
        df_export.to_excel(writer, index=False, startrow=6, sheet_name='Mayores Costos')
        
        workbook = writer.book
        worksheet = writer.sheets['Mayores Costos']
        
        # --- Cabecera Personalizada ---
        worksheet['A1'] = "CÁLCULO DE MAYORES COSTOS (Índices Reales)"
        worksheet['A2'] = f"Presupuesto Original: ${presupuesto}"
        worksheet['A3'] = f"Fecha Base: {fecha_base.strftime('%Y-%m')}"
        worksheet['A4'] = f"Índice Base ({tipo_indice}): {indice_base_valor}"
        
        money_fmt = '"$"#,##0.00'
        percent_fmt = '0.00%'
        
        # --- Formato de la tabla principal ---
        for row in range(8, 8 + len(df_export)):
            worksheet.cell(row=row, column=3).number_format = percent_fmt
            worksheet.cell(row=row, column=4).number_format = money_fmt

        # =========================================================
        # NUEVO CÓDIGO: AGREGAR FILAS TOTALIZADORAS AL FINAL
        # =========================================================
        
        # 1. Calculamos los valores matemáticos
        monto_mayor_costo = df_export['Importe'].iloc[-1]
        monto_original = float(presupuesto)
        monto_total_actualizado = monto_mayor_costo + monto_original

        # 2. Determinamos en qué fila escribir (justo debajo del bucle anterior)
        fila_footer_1 = 8 + len(df_export)
        fila_footer_2 = fila_footer_1 + 1
        fila_footer_3 = fila_footer_2 + 1

        # 3. Fila: Monto del Mayor Costo
        worksheet.cell(row=fila_footer_1, column=1, value="Monto del Mayor Costo")
        celda_mc = worksheet.cell(row=fila_footer_1, column=4, value=monto_mayor_costo)
        celda_mc.number_format = money_fmt

        # 4. Fila: Monto Original
        worksheet.cell(row=fila_footer_2, column=1, value="Monto Original")
        celda_mo = worksheet.cell(row=fila_footer_2, column=4, value=monto_original)
        celda_mo.number_format = money_fmt

        # 5. Fila: MONTO TOTAL ACTUALIZADO
        worksheet.cell(row=fila_footer_3, column=1, value="MONTO TOTAL ACTUALIZADO")
        celda_total = worksheet.cell(row=fila_footer_3, column=4, value=monto_total_actualizado)
        celda_total.number_format = money_fmt

    output.seek(0)
    return output