import os
import re
import requests
import pdfplumber
from datetime import datetime
from decimal import Decimal
from django.core.management.base import BaseCommand
from core.models import IndiceCAC
from playwright.sync_api import sync_playwright


class Command(BaseCommand):
    help = 'Scrapea el último índice de la CAC usando Playwright y lo guarda en la base de datos'

    def add_arguments(self, parser):
        parser.add_argument(
            'mes_objetivo',
            nargs='?',
            type=str,
            help='Mes a actualizar en formato MM-YYYY (ej. 02-2026)'
        )

    def limpiar_numero(self, valor_str):
        """Limpia el string del PDF y lo convierte a Decimal"""
        valor_limpio = valor_str.replace('f', '').strip()
        valor_limpio = valor_limpio.replace('.', '').replace(',', '.')
        return Decimal(valor_limpio)

    def extraer_numero_de_fila(self, fila):
        """
        Recorre las celdas de una fila buscando el formato 'xx.xxx,xx'
        (o 'xxx.xxx,xx') e ignora celdas vacías, None o porcentajes.
        """
        patron_indice = re.compile(r'^\d{1,3}(?:\.\d{3})+,\d{2}$')
        for celda in fila:
            if not celda:
                continue
            celda_limpia = str(celda).replace('f', '').strip()
            if patron_indice.match(celda_limpia):
                return self.limpiar_numero(celda_limpia)
        raise ValueError(f"No se encontró un número con formato válido en la fila: {fila}")

    def buscar_datos_mes(self, tablas, str_fecha_esperada):
        """
        Recorre todas las tablas y filas buscando el mes objetivo.
        Al ubicarlo en 'idx_fila', extrae:
        - Costo de Construcción en la fila anterior (idx_fila - 1)
        - Materiales en la misma fila de la fecha (idx_fila)
        - Mano de Obra en la fila siguiente (idx_fila + 1)
        """
        for tabla in tablas:
            for idx_fila, fila in enumerate(tabla):
                for celda in fila:
                    if not celda:
                        continue
                    celda_limpia = str(celda).replace('*', '').strip().upper()
                    if celda_limpia == str_fecha_esperada:
                        if idx_fila == 0 or idx_fila + 1 >= len(tabla):
                            raise IndexError(
                                f"Se encontró {str_fecha_esperada}, pero las filas contiguas están incompletas."
                            )
                        costo_const = self.extraer_numero_de_fila(tabla[idx_fila - 1])
                        materiales = self.extraer_numero_de_fila(tabla[idx_fila])
                        mano_obra = self.extraer_numero_de_fila(tabla[idx_fila + 1])
                        return costo_const, materiales, mano_obra
        return None

    def handle(self, *args, **kwargs):
        mes_objetivo = kwargs.get('mes_objetivo')

        # Si Railway no le pasa el mes, calculamos el MES ANTERIOR dinámicamente
        if not mes_objetivo:
            hoy = datetime.now()

            if hoy.month == 1:
                mes_anterior = 12
                anio = hoy.year - 1
            else:
                mes_anterior = hoy.month - 1
                anio = hoy.year

            # Formateamos a 'MM-YYYY' asegurando el cero a la izquierda (ej: '02' en vez de '2')
            mes_objetivo = f"{mes_anterior:02d}-{anio}"

            self.stdout.write(
                self.style.WARNING(f"Modo automático: Buscando el índice del mes anterior -> {mes_objetivo}")
            )

        # Convertimos el string a objeto date para consultar la BD
        fecha_obj = datetime.strptime(mes_objetivo, '%m-%Y').date()

        # Consultamos si ya existe en la base de datos
        if IndiceCAC.objects.filter(fecha=fecha_obj).exists():
            self.stdout.write(
                self.style.SUCCESS(f"La base de datos ya estaba actualizada para {mes_objetivo}.")
            )
            return  # Se corta la ejecución acá para no activar el scraper

        url_base = "https://www.cifrasonline.com.ar/indice-cac/"
        pdf_url = None

        self.stdout.write(self.style.WARNING("1. Abriendo navegador en segundo plano (Playwright)..."))

        # --- BLOQUE PLAYWRIGHT ---
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                page.goto(url_base)
                self.stdout.write("2. Buscando el botón del PDF...")

                xpath_boton = "xpath=/html/body/div[1]/main/div/section[3]/div[2]/div[3]/div/div/a[1]"

                elemento_pdf = page.locator(xpath_boton)
                elemento_pdf.wait_for(state="visible", timeout=10000)

                pdf_url = elemento_pdf.get_attribute('href')

                browser.close()

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error con Playwright: {e}"))
            return

        if not pdf_url:
            self.stdout.write(self.style.ERROR("No se obtuvo una URL válida."))
            return

        # --- CONVERSIÓN GOOGLE DRIVE ---
        self.stdout.write("3. Convirtiendo link de Google Drive...")
        match = re.search(r'/d/([a-zA-Z0-9_-]+)', pdf_url)

        if match:
            file_id = match.group(1)
            pdf_url = f"https://drive.google.com/uc?export=download&id={file_id}"

        # --- DESCARGA CON REQUESTS ---
        self.stdout.write("4. Descargando el archivo PDF real...")
        headers = {"User-Agent": "Mozilla/5.0"}
        pdf_response = requests.get(pdf_url, headers=headers)

        temp_pdf_name = "CAC_temp.pdf"
        with open(temp_pdf_name, 'wb') as f:
            f.write(pdf_response.content)

        # --- EXTRACCIÓN, VALIDACIÓN Y GUARDADO EN BD ---
        self.stdout.write("5. Extrayendo datos y actualizando BD...")
        try:
            with pdfplumber.open(temp_pdf_name) as p:
                tablas = p.pages[0].extract_tables()

            # Diccionario para mapear el número de mes al formato del PDF
            meses_espanol = {
                1: 'ENE', 2: 'FEB', 3: 'MAR', 4: 'ABR', 5: 'MAY', 6: 'JUN',
                7: 'JUL', 8: 'AGO', 9: 'SEP', 10: 'OCT', 11: 'NOV', 12: 'DIC'
            }

            # Formateamos el mes que esperamos encontrar (ej. 'SEP2026' o 'JUN2026')
            str_fecha_esperada = f"{meses_espanol[fecha_obj.month]}{fecha_obj.year}"

            # Buscamos dinámicamente el mes en todas las tablas del PDF
            resultado = self.buscar_datos_mes(tablas, str_fecha_esperada)

            if not resultado:
                self.stdout.write(
                    self.style.WARNING(
                        f"Alerta: No se encontró el período '{str_fecha_esperada}' en ninguna tabla del PDF. "
                        "Todavía no actualizaron el archivo en la página. Se cancela el guardado."
                    )
                )
                return

            costo_const, materiales, mano_obra = resultado

            self.stdout.write(
                self.style.SUCCESS(f"Validación exitosa: Se ubicó el período {str_fecha_esperada} en el PDF.")
            )

            # Guardamos en la base de datos
            obj, created = IndiceCAC.objects.update_or_create(
                fecha=fecha_obj,
                defaults={
                    'costo_construccion': costo_const,
                    'materiales': materiales,
                    'mano_obra': mano_obra
                }
            )

            accion = "Creado" if created else "Actualizado"
            self.stdout.write(
                self.style.SUCCESS(
                    f"¡Éxito! Registro {accion} para {mes_objetivo} -> "
                    f"Costo: {costo_const} | Mat: {materiales} | MO: {mano_obra}"
                )
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error en extracción o guardado: {e}"))

        finally:
            if os.path.exists(temp_pdf_name):
                os.remove(temp_pdf_name)