# 🏗️ Calculadora de Mayores Costos (Índice CAC)

Una aplicación web desarrollada en Django que automatiza la actualización de presupuestos de construcción aplicando los índices oficiales de la Cámara Argentina de la Construcción (CAC).

## 📖 Resumen del Proyecto

* **Situación:** En el sector de la construcción, la inflación exige actualizar constantemente los presupuestos originales. El proceso manual implica buscar el índice oficial (publicado mensualmente en formato PDF), extraer los valores y recalcular hojas de cálculo, lo que es propenso a errores humanos y consume tiempo.
* **Tarea:** Desarrollar una herramienta web automatizada que permita a los usuarios subir los parámetros de su presupuesto, consultar una base de datos histórica precisa y descargar un reporte financiero estandarizado en Excel.
* **Acción:** * Construí una aplicación web con **Django** y **Pandas** para procesar la lógica de negocio y cálculos de incidencia matemática.
  * Implementé un pipeline ETL utilizando **Playwright** para el web scraping dinámico y **pdfplumber** para la extracción de texto, sorteando obstáculos de infraestructura (visores de Google Drive).
  * Generé reportes dinámicos utilizando **openpyxl** para preservar formatos de moneda y porcentajes en los entregables.
* **Resultado:** Un sistema robusto que reduce un proceso manual de varios minutos a un solo clic. La aplicación mantiene una base de datos histórica actualizada y exporta un archivo Excel detallado con los cálculos de "Mayores Costos" listos para presentar.

## 🛠️ Stack Tecnológico
* **Backend:** Python, Django
* **Data & ETL:** Pandas, Playwright, pdfplumber, Requests, re (RegEx)
* **Exportación:** Openpyxl
* **Frontend:** HTML5, CSS3 (con soporte para Modo Oscuro nativo)
