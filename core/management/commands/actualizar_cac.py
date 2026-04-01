# core/management/commands/actualizar_cac.py
import os
import re
import requests
import pdfplumber
from datetime import datetime
from decimal import Decimal
from django.core.management.base import BaseCommand
from core.models import IndiceCAC

# Nueva importación de Playwright (síncrona para simplificar)
from playwright.sync_api import sync_playwright

class Command(BaseCommand):
    help = 'Scrapea el último índice de la CAC usando Playwright y lo guarda en la base de datos'

    def add_arguments(self, parser):
        parser.add_argument('mes_objetivo', type=str, help='Mes a actualizar en formato MM-YYYY (ej. 02-2026)')

    def limpiar_numero(self, valor_str):
        """Limpia el string del PDF y lo convierte a Decimal"""
        valor_limpio = valor_str.replace('f', '').strip()
        valor_limpio = valor_limpio.replace('.', '').replace(',', '.')
        return Decimal(valor_limpio)

    def handle(self, *args, **kwargs):
        mes_objetivo = kwargs['mes_objetivo']
        url_base = "https://www.cifrasonline.com.ar/indice-cac/"
        pdf_url = None
        
        self.stdout.write(self.style.WARNING("1. Abriendo navegador en segundo plano (Playwright)..."))
        
        # --- BLOQUE PLAYWRIGHT ---
        try:
            with sync_playwright() as p:
                # Lanzamos Chromium en modo headless (invisible)
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                
                page.goto(url_base)
                self.stdout.write("2. Buscando el botón del PDF...")
                
                xpath_boton = "xpath=/html/body/div[1]/main/div/section[3]/div[2]/div[3]/div/div/a[1]"
                
                # Localizamos el elemento y esperamos a que sea visible (máx 10 seg)
                elemento_pdf = page.locator(xpath_boton)
                elemento_pdf.wait_for(state="visible", timeout=10000)
                
                # Extraemos el enlace
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
        # (Mantenemos requests porque para Google Drive directo es lo más veloz y estable)
        self.stdout.write("4. Descargando el archivo PDF real...")
        headers = {"User-Agent": "Mozilla/5.0"}
        pdf_response = requests.get(pdf_url, headers=headers)
        
        temp_pdf_name = "CAC_temp.pdf"
        with open(temp_pdf_name, 'wb') as f:
            f.write(pdf_response.content)

        # --- EXTRACCIÓN Y GUARDADO EN BD ---
        self.stdout.write("5. Extrayendo datos y actualizando BD...")
        try:
            with pdfplumber.open(temp_pdf_name) as p:
                tablas = p.pages[0].extract_tables()

            costo_const = self.limpiar_numero(tablas[1][1][3])
            materiales = self.limpiar_numero(tablas[1][2][3])
            mano_obra = self.limpiar_numero(tablas[1][3][3])

            fecha_obj = datetime.strptime(mes_objetivo, '%m-%Y').date()

            obj, created = IndiceCAC.objects.update_or_create(
                fecha=fecha_obj,
                defaults={
                    'costo_construccion': costo_const,
                    'materiales': materiales,
                    'mano_obra': mano_obra
                }
            )

            accion = "Creado" if created else "Actualizado"
            self.stdout.write(self.style.SUCCESS(
                f"✅ ¡Éxito! Registro {accion} para {mes_objetivo} -> Costo: {costo_const} | Mat: {materiales} | MO: {mano_obra}"
            ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error en extracción o guardado: {e}"))
            
        finally:
            if os.path.exists(temp_pdf_name):
                os.remove(temp_pdf_name)