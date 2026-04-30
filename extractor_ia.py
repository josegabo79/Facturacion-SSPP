import os
import time
import json
import re          
import pandas as pd
import openpyxl
import google.generativeai as genai
import pandas as pd

import sys

# Solo importamos las herramientas de sonido y notificaciones si estamos en Windows
if sys.platform == "win32":
    import winsound
    from plyer import notification

# Importamos nuestros módulos locales
import config
from motor_matematico import calcular_cu_ponderados

# =====================================================================
# NUEVO: FUNCIÓN AUXILIAR DE NOTIFICACIÓN DE ERRORES
# =====================================================================
def notificar_error(archivo, motivo):
    """Lanza una notificación visual y sonora cuando un archivo falla por completo."""
    if sys.platform == "win32":
        try:
            # Sonido crítico/error nativo de Windows
            winsound.MessageBeep(winsound.MB_ICONHAND) 
            notification.notify(
                title="⚠️ Fallo IA - SSPP",
                message=f"El archivo {archivo} falló:\n{motivo}",
                app_name="Guardián SSPP",
                timeout=7  
            )
        except:
            pass
def procesar_y_guardar_factura_vision(ruta_pdf, archivo, nombre_edificio):
    # --- FILTRO DE MEMORIA INMEDIATA ---
    if archivo in config.archivos_procesados_memoria:
        return
    config.archivos_procesados_memoria.add(archivo)
    
    # --- FILTRO ANTI-DUPLICADOS EN EXCEL ---
    if os.path.exists(config.ruta_excel):
        try:
            df_existente = pd.read_excel(config.ruta_excel)
            if 'Archivo_Origen' in df_existente.columns and archivo in df_existente['Archivo_Origen'].values:
                print(f"⏭️ El archivo '{archivo}' ya está en el Excel. Omitiendo procesamiento.")
                return
        except Exception as e:
            pass 

    print(f"\n👁️ Gemini Visión analizando: {archivo} (Usando API Key #{config.indice_key_actual + 1})...")
    print(f"{'='*60}")
    
    instruccion = """
    Actúa como un sistema experto en lectura de facturas complejas en PDF con OCR imperfecto.
    Tu tarea es extraer los datos clave y devolverlos ÚNICAMENTE en formato JSON válido puro (sin bloques de código markdown, sin texto adicional).
    El documento tiene un diseño de varias columnas. Encabezados y valores al frente de cada detalle o debajo en totales.
    Asegúrate de escanear visualmente los cuadrantes completos cada nombre tiene su respectivo número.
    VALIDACIÓN: - Si hay múltiples posibles valores, elige el más coherente con el contexto (ej: subtotales vs totales) - Evita valores aislados sin contexto claro. 
    PROBLEMA CLAVE A EVITAR: No confundas SUBTOTALES con TOTALES.
    JERARQUÍA:Identifica niveles: - Totales principales - Subtotales - Componentes (ej: generación, transmisión, distribución)
    TOLERANCIA A ERRORES OCR: Corrige mentalmente errores comunes: - números pegados - textos cortados - columnas corridas
    No inventes datos. Si no encuentras un dato con suficiente confianza, devuélvelo como null.
    REGLA Comercializadores: AIR-e sus valores importantes estan sombreados en la factura. 

    Devuelve un JSON estructurado así:
    {
        "campo": { "valor": "...", "confianza": "alta | media | baja", "fuente": "texto cercano del documento" }
    } 

    OBLIGATORIO: Utiliza EXACTAMENTE las siguientes claves en tu JSON con las 3 propiedades::
    {
        "Comercializador": "Nombre de la empresa" (AIR-e, EPM, Enertotal)
        "Contrato": "Numero de NIC, Contrato, Cliente",
        "Nivel_tension": "Ejemplo: N2",
        "Periodo": "Ejemplo: 01/03/2024 al 31/03/2024",
        "Mes_pago": Mes y año en que se debe realizar el pago (ej. 03/2026).
        "CU_Total": Nombres posibles: [Costo Unitario total en $ del kW/h] o [Tarifa promedio ($/Kwh) (AIR-e Septima fila)] o [$/Kwh de Energía Activa]. 
        "Consumo_Total": 0.0, Total Energía Activa en Kwh (Kw/h).
        "Subtotal_Generacion": 0.0, [Toma el valor de la sección Generación exclusivamente: Total a pagar Generación (G)] o [Al frente de: Total Costo de la generación].
        "Subtotal_Transporte_Nac": 0.0, Puede aparecer en la factura bajo los nombres: [Costo del transporte] o [trasnmisión] o  [STN].
        "Subtotal_Transporte_Reg": 0.0, Puede aparecer en la factura bajo los nombres: [Costo del transporte Regional] o [trasnmisión Regional] o [STR].
        "Subtotal_Distribucion": 0.0, Nombres posibles: [Costo de la distribución] o [SDL].
        "Subtotal_Comercializacion": 0.0, Costo de la comercialización.
        "Subtotal_Perdidas": 0.0, Costo de las perdidas. 
        "Subtotal_Restricciones": 0.0, ó Otros cargos regulados
        "Total_Pagar": El monto total a pagar de la factura.
        "Subtotal": Valor que corresponde a lo cobrado solamente por energía, Valor facturado energía.
        "Energia_reactiva": Valor cobrado por energía reactiva en pesos.
        "Valor_aseo": Valor de la tasa por aseo cobrada a través de terceros.
        "Valor_seguridad": Valor de la tasa de seguridad y/o convivencia.
        "Alumbrado_publico": Valor del impuesto de alumbrado público.
        "Cobros_Atipicos": Si detectas conceptos de cobro inusuales (reconexiones, multas, seguros, financiaciones), lístalos aquí separados por comas. Si no hay, devuelve "Ninguno".
    }
    """

    intentos_ia = 1
    datos_factura_anidados = None

    while True:
        try:
            archivo_ia = config.cliente.files.upload(file=ruta_pdf)
            while archivo_ia.state.name == "PROCESSING":
                time.sleep(2)
                archivo_ia = config.cliente.files.get(name=archivo_ia.name)

            respuesta = config.cliente.models.generate_content(
                model='gemini-flash-latest', 
                contents=[archivo_ia, instruccion]
            )

            try:
                tokens_in = respuesta.usage_metadata.prompt_token_count
                tokens_out = respuesta.usage_metadata.candidates_token_count
                total_tokens = tokens_in + tokens_out
                costo_usd = ((tokens_in / 1000000) * 0.075) + ((tokens_out / 1000000) * 0.30)
                print(f"📊 Tokens: {total_tokens} | Costo aprox: ${costo_usd * 4000:.2f} COP")
            except Exception:
                pass

            match = re.search(r'\{.*\}', respuesta.text, re.DOTALL)
            datos_factura_anidados = json.loads(match.group(0)) if match else json.loads(respuesta.text)
            
            config.cliente.files.delete(name=archivo_ia.name) 
            break 
            
        except Exception as e:
            mensaje_error = str(e).lower()

            if "429" in mensaje_error or "quota" in mensaje_error or "exhausted" in mensaje_error:
                print(f"⏳ Límite de cuota alcanzado en la API Key #{config.indice_key_actual + 1}.")
                config.rotar_api_key()
                intentos_ia += 1
                if intentos_ia % len(config.API_KEYS) == 0:
                    print("⚠️ Todas las API Keys están saturadas. Pausa profunda de 60s...")
                    time.sleep(60)
                else:
                    time.sleep(2)
                    
            elif "503" in mensaje_error or "unavailable" in mensaje_error or "high demand" in mensaje_error:
                print("⏳ Servidores de Google muy ocupados (Error 503). Esperando 15 segundos para reintentar...")
                time.sleep(15)
                
            else:
                print(f"✗ Error procesando la IA: {e}")
                # --- ALERTA DE ERROR IA ---
                notificar_error(archivo, "Error crítico de lectura o subida a Google AI.")
                return
            
    if not datos_factura_anidados: 
        # --- ALERTA DE ERROR DE JSON VACÍO ---
        notificar_error(archivo, "La IA no devolvió datos estructurados legibles.")
        return

    if config.MOSTRAR_RAZONAMIENTO_CONSOLA:
        print("\n🧠 --- RAZONAMIENTO DE LA IA ---")
        
    datos_planos = {}
    for clave, contenido in datos_factura_anidados.items():
        if isinstance(contenido, dict) and "valor" in contenido:
            valor_real = contenido["valor"]
            datos_planos[clave] = valor_real
            
            if config.MOSTRAR_RAZONAMIENTO_CONSOLA:
                confianza = contenido.get("confianza", "desconocida").upper()
                fuente = contenido.get("fuente", "")
                icono = "🟢" if confianza == "ALTA" else "🟡" if confianza == "MEDIA" else "🔴"
                print(f"{icono} {clave}: {valor_real}")
                print(f"    └─ {confianza} | {fuente}")
        else:
            datos_planos[clave] = contenido
            if config.MOSTRAR_RAZONAMIENTO_CONSOLA:
                print(f"⚪ {clave}: {contenido}")
                
    if config.MOSTRAR_RAZONAMIENTO_CONSOLA:
        print("-" * 32 + "\n")

    # Usamos el motor matemático
    datos_finales = calcular_cu_ponderados(datos_planos)
    
    datos_finales["Edificio"] = nombre_edificio
    datos_finales["Archivo_Origen"] = archivo
    
    df_nueva = pd.DataFrame([datos_finales])

    print(f"💾 Guardando en Excel...")
    while True:
        try:
            if os.path.exists(config.ruta_excel):
                df_existente = pd.read_excel(config.ruta_excel)
                df_final = pd.concat([df_existente, df_nueva], ignore_index=True)
            else:
                df_final = df_nueva
            
            df_final.to_excel(config.ruta_excel, index=False)
            
            try:
                wb = openpyxl.load_workbook(config.ruta_excel)
                hoja = wb.active
                for col in hoja.columns:
                    hoja.column_dimensions[col[0].column_letter].width = 15
                wb.save(config.ruta_excel)
            except: pass 

            print(f"✅ ¡ÉXITO! Datos guardados en {os.path.basename(config.ruta_excel)}\n")

            try:
                # Sonido de éxito
                winsound.MessageBeep(winsound.MB_ICONASTERISK)
                notification.notify(
                    title="🤖 Guardián IA - SSPP",
                    message=f"¡Éxito! La factura {archivo} se guardó.",
                    app_name="Guardián SSPP",
                    timeout=5  
                )
            except: 
                pass

            break 
            
        except PermissionError:
            print(f"⚠️  ¡EXCEL BLOQUEADO! Por favor, ciérralo. Reintentando en 10s...")
            time.sleep(10)
        except Exception as e:
            print(f"✗ Error inesperado al escribir el Excel: {e}")
            # --- ALERTA DE ERROR AL GUARDAR ---
            notificar_error(archivo, "Fallo al intentar escribir el archivo Excel.")
            break


# 1. Configuración de la llave (Usa la misma que tienes en tus otros archivos)
genai.configure(api_key="AIzaSyA1Q4UL8doXVBPUjmBmDoMBv0Ze7oJCJlc")

# 2. Definición del modelo 
model = genai.GenerativeModel('gemini-flash-latest')

def consultar_chatbot(pregunta, dataframe):
    # Convertimos las últimas filas del Excel a texto para darle contexto a la IA
    # Solo enviamos lo necesario para no saturar el prompt
    datos_recientes = dataframe.tail(15).to_string(index=False)
    
    prompt_analisis = f"""
    Eres el Analista Senior de Energía de Pactia. 
    Tu base de datos es la siguiente tabla de facturas procesadas:
    
    {datos_recientes}
    
    Pregunta del usuario: {pregunta}
    
    Instrucciones:
    - Responde de forma clara, técnica y resumina. 
    - Si detectas valores de Energía Reactiva altos o penalidades, resáltalos.
    - Si comparas sedes, menciona el nombre de la sede exacto.
    - La respuesta debe ser corta y concreta
    - SI la pregunta pide comparar valores, añade al final EXACTAMENTE la etiqueta '---GRAFICA---' seguida de una tabla de formato CSV de dos columnas (Edificio, Valor). No uses formato markdown para la tabla.
    """
    
    # Ahora 'model' ya funcionará porque lo definimos arriba
    response = model.generate_content(prompt_analisis)
    return response.text
