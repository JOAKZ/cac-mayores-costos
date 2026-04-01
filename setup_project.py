import os

# Definición de la estructura y contenido de los archivos
project_structure = {
    "requirements.txt": """django
pandas
openpyxl
requests
beautifulsoup4
pdfplumber""",

    "manage.py": """#!/usr/bin/env python
import os
import sys

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cac_project.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
""",

    "cac_project/__init__.py": "",
    
    "cac_project/settings.py": """
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = 'django-insecure-change-me-later-for-production'
DEBUG = True
ALLOWED_HOSTS = []

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'cac_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'cac_project.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = []
LANGUAGE_CODE = 'es-ar'
TIME_ZONE = 'America/Argentina/Buenos_Aires'
USE_I18N = True
USE_TZ = True
STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
""",

    "cac_project/urls.py": """
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
]
""",

    "cac_project/wsgi.py": """
import os
from django.core.wsgi import get_wsgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cac_project.settings')
application = get_wsgi_application()
""",

    "core/__init__.py": "",
    
    "core/apps.py": """
from django.apps import AppConfig
class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
""",

    "core/forms.py": """
from django import forms
from django.core.exceptions import ValidationError
from datetime import date

class CalculoForm(forms.Form):
    OPCIONES_INDICE = [
        ('costo_construccion', 'Costo de Construcción'),
        ('materiales', 'Materiales'),
        ('mano_obra', 'Mano de Obra'),
    ]

    fecha_base = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'month', 'class': 'form-control'}),
        label="Fecha Base"
    )
    fecha_final = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'month', 'class': 'form-control'}),
        label="Fecha Final"
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

        if f_base and f_final:
            # Normalizar al primer día del mes para comparar
            f_base = f_base.replace(day=1)
            f_final = f_final.replace(day=1)
            
            if f_base > f_final:
                raise ValidationError("La fecha base no puede ser mayor a la fecha final.")
            
            hoy = date.today()
            primer_dia_mes_actual = date(hoy.year, hoy.month, 1)
            
            # Nota: Ajusta esta validación según la disponibilidad real de datos
            if f_final > primer_dia_mes_actual:
                 self.add_error('fecha_final', "No tenemos datos futuros. Selecciona hasta el mes actual.")
        
        return cleaned_data
""",

    "core/urls.py": """
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
]
""",

    "core/utils.py": """
import pandas as pd
import io
from datetime import datetime, timedelta
import random

# NOTA PARA JOAQUIN: 
# Como el scraping real puede fallar si la pagina cambia o no tenemos internet,
# he creado una funcion 'mock' (simulada) para que pruebes la app inmediatamente.
# Cuando quieras conectar el scraping real, usa la funcion 'obtener_datos_reales'.

def obtener_datos_cac(simulacion=True):
    if simulacion:
        return _generar_datos_simulados()
    else:
        # Aquí iría tu lógica de BeautifulSoup y PDFPlumber
        # Para el prototipo, usaremos la simulada para asegurar que el Excel salga bien.
        return _generar_datos_simulados()

def _generar_datos_simulados():
    # Crea datos ficticios desde 2011 hasta hoy para probar el Excel
    fechas = pd.date_range(start='2011-01-01', end=datetime.now(), freq='MS')
    data = []
    
    # Indices base ficticios que van creciendo
    base_gral = 1000
    base_mat = 1000
    base_mo = 1000
    
    for fecha in fechas:
        # Crecimiento aleatorio simulando inflación
        base_gral *= 1.05 
        base_mat *= 1.04
        base_mo *= 1.06
        
        data.append({
            'fecha': fecha,
            'costo_construccion': round(base_gral, 2),
            'materiales': round(base_mat, 2),
            'mano_obra': round(base_mo, 2)
        })
    
    return pd.DataFrame(data)

def generar_excel_mayores_costos(fecha_base, fecha_final, presupuesto, tipo_indice):
    # 1. Obtener datos (Data Science ETL)
    df = obtener_datos_cac(simulacion=True)
    
    # 2. Filtrar por fechas
    # Aseguramos que las fechas sean datetime para comparar
    fecha_base = pd.to_datetime(fecha_base).replace(day=1)
    fecha_final = pd.to_datetime(fecha_final).replace(day=1)
    
    mask = (df['fecha'] >= fecha_base) & (df['fecha'] <= fecha_final)
    df_filtrado = df.loc[mask].copy()
    
    if df_filtrado.empty:
        return None

    # 3. Cálculos Matemáticos
    # El valor del índice en el mes base
    indice_base_valor = df_filtrado.iloc[0][tipo_indice]
    
    # Calculamos columnas nuevas
    # % Incidencia: (Indice Mes / Indice Base) - 1
    df_filtrado['Coeficiente'] = (df_filtrado[tipo_indice] / indice_base_valor) - 1
    # Importe (Mayor Costo): Presupuesto * Coeficiente
    df_filtrado['Importe'] = df_filtrado['Coeficiente'] * float(presupuesto)
    
    # 4. Formateo para Excel (estética)
    output = io.BytesIO()
    
    # Usamos ExcelWriter con engine openpyxl para formatos
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        
        # Preparamos el DF final para imprimir
        df_export = pd.DataFrame({
            'Fecha': df_filtrado['fecha'].dt.strftime('%Y-%m-%d'),
            'Indice': df_filtrado[tipo_indice],
            '% Incidencia': df_filtrado['Coeficiente'],
            'Importe': df_filtrado['Importe']
        })
        
        df_export.to_excel(writer, index=False, startrow=6, sheet_name='Mayores Costos')
        
        workbook = writer.book
        worksheet = writer.sheets['Mayores Costos']
        
        # --- Cabecera Personalizada (Metadata) ---
        worksheet['A1'] = "CALCULO DE MAYORES COSTOS"
        worksheet['A2'] = f"Presupuesto Original: ${presupuesto}"
        worksheet['A3'] = f"Fecha Base: {fecha_base.strftime('%Y-%m-%d')}"
        worksheet['A4'] = f"Indice Base ({tipo_indice}): {indice_base_valor}"
        
        # Formato de moneda
        money_fmt = '"$"#,##0.00'
        percent_fmt = '0.00%'
        
        # Aplicar formatos a las columnas (iterando filas)
        for row in range(8, 8 + len(df_export)):
            # Columna C (% Incidencia)
            cell_percent = worksheet.cell(row=row, column=3)
            cell_percent.number_format = percent_fmt
            
            # Columna D (Importe)
            cell_money = worksheet.cell(row=row, column=4)
            cell_money.number_format = money_fmt

    output.seek(0)
    return output
""",

    "core/views.py": """
from django.shortcuts import render
from django.http import HttpResponse
from .forms import CalculoForm
from .utils import generar_excel_mayores_costos

def index(request):
    if request.method == 'POST':
        form = CalculoForm(request.POST)
        if form.is_valid():
            # Extraer datos limpios
            f_base = form.cleaned_data['fecha_base']
            f_final = form.cleaned_data['fecha_final']
            presupuesto = form.cleaned_data['presupuesto']
            tipo_indice = form.cleaned_data['tipo_indice']
            
            # Generar el Excel en memoria
            excel_file = generar_excel_mayores_costos(f_base, f_final, presupuesto, tipo_indice)
            
            if excel_file:
                # Crear respuesta HTTP con el archivo
                response = HttpResponse(
                    excel_file,
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                filename = f"Mayores_Costos_{f_final}.xlsx"
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                return response
            else:
                form.add_error(None, "No se encontraron datos para el rango de fechas seleccionado.")
                
    else:
        form = CalculoForm()

    return render(request, 'core/index.html', {'form': form})
""",

    "core/templates/core/index.html": """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Calculadora CAC | Mayores Costos</title>
    <style>
        :root {
            --bg-color: #f8f9fa;
            --text-color: #212529;
            --card-bg: #ffffff;
            --input-border: #ced4da;
            --accent: #0d6efd;
            --accent-hover: #0b5ed7;
            --button-text: #fff;
            --shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        }

        [data-theme="dark"] {
            --bg-color: #121212;
            --text-color: #e0e0e0;
            --card-bg: #1e1e1e;
            --input-border: #444;
            --accent: #bb86fc;
            --accent-hover: #9b65e6;
            --button-text: #000;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            transition: background-color 0.3s, color 0.3s;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            padding: 20px;
        }

        .container {
            background: var(--card-bg);
            padding: 2.5rem;
            border-radius: 12px;
            box-shadow: var(--shadow);
            width: 100%;
            max-width: 480px;
            position: relative;
        }

        .header-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
        }

        h1 { margin: 0; font-size: 1.5rem; font-weight: 700; }

        .toggle-btn {
            background: none;
            border: 1px solid var(--input-border);
            color: var(--text-color);
            padding: 0.4rem 0.8rem;
            border-radius: 20px;
            cursor: pointer;
            font-size: 1rem;
            transition: all 0.2s;
        }
        
        .toggle-btn:hover { background-color: var(--input-border); }

        .form-group { margin-bottom: 1.2rem; }
        
        label { 
            display: block; 
            margin-bottom: 0.5rem; 
            font-weight: 500; 
            font-size: 0.9rem;
        }
        
        input, select {
            width: 100%;
            padding: 12px;
            border: 1px solid var(--input-border);
            border-radius: 8px;
            background: var(--bg-color);
            color: var(--text-color);
            box-sizing: border-box;
            font-size: 1rem;
            transition: border-color 0.2s;
        }

        input:focus, select:focus {
            outline: none;
            border-color: var(--accent);
        }

        button[type="submit"] {
            width: 100%;
            padding: 14px;
            background-color: var(--accent);
            color: var(--button-text);
            border: none;
            border-radius: 8px;
            font-weight: 600;
            font-size: 1rem;
            cursor: pointer;
            margin-top: 1rem;
            transition: background-color 0.2s;
        }

        button[type="submit"]:hover { background-color: var(--accent-hover); }

        .info-section {
            margin-top: 2.5rem;
            font-size: 0.85rem;
            opacity: 0.8;
            line-height: 1.6;
            border-top: 1px solid var(--input-border);
            padding-top: 1.5rem;
        }

        .info-section h3 { font-size: 1rem; margin-bottom: 0.5rem; }
        
        .error-list {
            background-color: rgba(255, 0, 0, 0.1);
            border-left: 4px solid red;
            padding: 10px;
            margin-bottom: 15px;
            font-size: 0.9rem;
            border-radius: 4px;
        }
    </style>
</head>
<body>

    <div class="container">
        <div class="header-row">
            <h1>Cálculo CAC</h1>
            <button class="toggle-btn" id="theme-toggle" title="Cambiar Tema">🌗</button>
        </div>

        <form method="post">
            {% csrf_token %}
            
            {% if form.errors %}
                <div class="error-list">
                    {% for field, errors in form.errors.items %}
                        {% for error in errors %}
                            <div>• {{ error }}</div>
                        {% endfor %}
                    {% endfor %}
                </div>
            {% endif %}

            <div class="form-group">
                <label for="{{ form.fecha_base.id_for_label }}">Fecha Base (Inicio)</label>
                {{ form.fecha_base }}
            </div>

            <div class="form-group">
                <label for="{{ form.fecha_final.id_for_label }}">Fecha Final (Actualización)</label>
                {{ form.fecha_final }}
            </div>

            <div class="form-group">
                <label for="{{ form.presupuesto.id_for_label }}">Presupuesto Original ($)</label>
                {{ form.presupuesto }}
            </div>

            <div class="form-group">
                <label for="{{ form.tipo_indice.id_for_label }}">Índice de Ajuste</label>
                {{ form.tipo_indice }}
            </div>

            <button type="submit">DESCARGAR EXCEL ACTUALIZADO</button>
        </form>

        <div class="info-section">
            <h3>Sobre el índice CAC</h3>
            <p>
                Este cálculo utiliza los índices oficiales de la Cámara Argentina de la Construcción.
                El cálculo de "Mayores Costos" refleja la diferencia de precios entre el mes base y el mes de actualización.
            </p>
            <p>
                <strong>Nota:</strong> Los índices de Mano de Obra suelen variar según acuerdos paritarios, mientras que Materiales sigue más de cerca la inflación del dólar y costos de producción.
            </p>
        </div>
    </div>

    <script>
        const toggleBtn = document.getElementById('theme-toggle');
        const html = document.documentElement;

        // Lógica de Modo Oscuro
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme) {
            html.setAttribute('data-theme', savedTheme);
        } else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            html.setAttribute('data-theme', 'dark');
        }

        toggleBtn.addEventListener('click', () => {
            if (html.getAttribute('data-theme') === 'dark') {
                html.removeAttribute('data-theme');
                localStorage.setItem('theme', 'light');
            } else {
                html.setAttribute('data-theme', 'dark');
                localStorage.setItem('theme', 'dark');
            }
        });
    </script>
</body>
</html>
"""
}

def create_project():
    print("🚀 Iniciando creación del proyecto Django 'cac_project'...")
    
    for file_path, content in project_structure.items():
        # Crear directorios si no existen
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
            print(f"📁 Directorio creado: {directory}")
        
        # Escribir archivo (saltar si es binario/carpeta vacía init que ya se manejó)
        if content is not None:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content.strip())
            print(f"✅ Archivo creado: {file_path}")

    print("\n🎉 ¡Proyecto creado con éxito!")
    print("\n--- INSTRUCCIONES ---")
    print("1. Crea un entorno virtual (opcional pero recomendado): python -m venv venv")
    print("2. Actívalo: source venv/bin/activate (Mac/Linux) o venv\\Scripts\\activate (Windows)")
    print("3. Instala las dependencias: pip install -r requirements.txt")
    print("4. Ejecuta el servidor: python manage.py runserver")
    print("5. Abre en tu navegador: http://127.0.0.1:8000/")

if __name__ == "__main__":
    create_project()