import pandas as pd
from google import genai
import config
import streamlit as st
import time

# --- CONEXIÓN SEGURA EN LA NUBE PARA GEMINI ---  
try:
    # El código va a la caja fuerte de Streamlit y saca la llave llamada "GEMINI_API_KEY"
    llave_secreta = st.secrets["GEMINI_API_KEY"]
    cliente_ia = genai.Client(api_key=llave_secreta)
except Exception as e:
    st.error("⚠️ Error de seguridad: No se encontró la llave de Gemini en los Secretos.")
    cliente_ia = None

def consultar_chatbot(pregunta, dataframe):
    if not cliente_ia:
        return "⚠️ Error: Cliente de IA no configurado."

    # Convertimos a CSV exacto para no saturar a la IA ni demorarla con espacios
    datos_completos = dataframe.to_csv(index=False)
    
    # ESTE ES EXACTAMENTE TU PROMPT ORIGINAL, SIN MODIFICAR:
    prompt_analisis = f"""
    Eres el Analista Senior de Energía de Pactia. 
    Tu base de datos es la siguiente tabla de facturas procesadas en formato CSV:
    
    {datos_completos}
    
    Pregunta del usuario: {pregunta}
    
    Instrucciones:
    - Responde de forma clara técnica y no muy extensa. 
    - Si detectas valores de Energía Reactiva altos (mayores de 500.000) o penalidades, resáltalos.
    - Si comparas sedes, menciona el nombre de la sede exacto.
    - Nota: Los nombres de los edificios pueden variar. Si la tabla de tu respuesta tiene 6 edificios, el CSV debe tener las 6 columnas de esos edificios.

    2. DEBES escribir la etiqueta ---GRAFICA_TORTA--- seguida de un salto de línea y un CSV
    Categoria,Valor
    Pon el promedio de los 6 componentes exactos: Generación (CU_Generación), Transmisión (Cu_Transmisión), Distribución (CU_Transporte_Nacional + CU_Transporte_Regional), Comercialización (CU_Comercializacion), Restricciones (CU_Restricciones), Pérdidas (CU_Perdidas). 
    Si preguntan por un solo edificio y no tiene componentes poner el valor de Costo Unitario (CU_Total) y no poner columnas de componentes

    REGLAS DE FORMATO Y REDACCIÓN (MUY IMPORTANTE):
    - NUNCA uses formato matemático ni LaTeX. ESTÁ TOTALMENTE PROHIBIDO encerrar texto o números entre signos de dólar ($ ... $).
    - Si vas a mencionar un valor monetario, debes "escapar" el signo de dólar usando una barra invertida (ejemplo: \\$500.000) o usar la palabra "COP" (ejemplo: COP 500.000).
    - Usa negritas (**) solo para resaltar palabras clave completas, asegurándote de dejar espacios alrededor de los asteriscos. No pegues asteriscos a números o símbolos especiales.
    """    
    
    # --- SISTEMA ANTICAÍDAS Y TOLERANCIA AL TRÁFICO (REINTENTOS AUTOMÁTICOS) ---
    max_reintentos = 3 
    
    for intento in range(max_reintentos):
        try:
            respuesta = cliente_ia.models.generate_content(
                model='gemini-2.0-flash', 
                contents=prompt_analisis
            )
            return respuesta.text
            
        except Exception as e:
            error_msg = str(e)
            # Si el servidor está saturado (503) o superamos cuota (429), respira 5 segs y repite
            if "503" in error_msg or "UNAVAILABLE" in error_msg or "429" in error_msg:
                if intento < max_reintentos - 1:
                    time.sleep(5)  
                    continue       
            
            # Si definitivamente falló tras 3 intentos, devuelve error amigable
            return "⚠️ Los servidores de IA están demasiado saturados analizando la base de datos en este momento. Por favor, intenta de nuevo en unos segundos."