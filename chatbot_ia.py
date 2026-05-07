import pandas as pd
from google import genai
import config
import streamlit as st

# --- CONEXIÓN SEGURA EN LA NUBE PARA GEMINI ---
try:
    # El código va a la caja fuerte de Streamlit y saca la llave llamada "GEMINI_API_KEY"
    llave_secreta = st.secrets["GEMINI_API_KEY"]
    cliente = genai.Client(api_key=llave_secreta)
except Exception as e:
    st.error("⚠️ Error de seguridad: No se encontró la llave de Gemini en los Secretos.")

def consultar_chatbot(pregunta, dataframe):
    # Convertimos las últimas filas del Excel a texto para darle contexto a la IA
    # Solo enviamos lo necesario para no saturar el prompt
    
    datos_completos = dataframe.to_string(index=False)
    
    prompt_analisis = f"""
    Eres el Analista Senior de Energía de Pactia. 
    Tu base de datos es la siguiente tabla de facturas procesadas:
    
    {datos_completos}
    
    Pregunta del usuario: {pregunta}
    
    Instrucciones:
    - Responde de forma clara, técnica y resumina. 
    - Si detectas valores de Energía Reactiva altos (mayores de $500.000) o penalidades, resáltalos.
    - Si comparas sedes, menciona el nombre de la sede exacto.
    - Nota: Los nombres de los edificios pueden estar escritos con o sin tildes (ej. Buro 51 o Buró 51). Trátalos como si fueran el mismo.
    - La respuesta debe ser corta y concreta

    REGLAS ESTRICTAS PARA GENERAR GRÁFICAS:
    SIEMPRE debes incluir DOS bloques al final de tu respuesta EXACTAMENTE con esta estructura (no uses bloques de código markdown, solo texto plano):

    1. DEBES escribir la etiqueta ---GRAFICA_BARRA--- seguida de un salto de línea y un CSV para evolución en el tiempo:
    - La Columna 1 SIEMPRE debe ser "Mes" (columna Mes_pago) (orden cronológico).
    - Traer los datos de los meses que pida el usuario o si no pide nada traer 4 ulimos meses.  
    - MODO SERIES (Comparativa total): Si piden comparar o ver todos los edificios, usa múltiples columnas incluyendo TODOS los edificios. 
    - Traer los datos que pida el usuario para El Valor en las series: consumo (columna Consumo_Total), costo (valor) (Columna "Subtotal") o CU (Columna CU_Total). Si no pide consumo o CU, traer datos del costo.
    - REGLA CRÍTICA: PROHIBIDO RESUMIR. NO uses "etc". El CSV debe contener las columnas de TODOS los edificios sin omitir ninguno. Si la tabla de tu respuesta tiene 6 edificios, el CSV debe tener las 6 columnas de esos edificios.

    2. DEBES escribir la etiqueta ---GRAFICA_TORTA--- seguida de un salto de línea y un CSV
    Categoria,Valor
    Pon el promedio de los 6 componentes exactos: Generación (CU_Generación), Transmisión (Cu_Transmisión), Distribución (CU_Transporte_Nacional + CU_Transporte_Regional), Comercialización (CU_Comercializacion), Restricciones (CU_Restricciones), Pérdidas (CU_Perdidas). 
    Si preguntan por un solo edificio y no tiene componentes poner el valor de Costo Unitario (CU_Total)  y no poner columnas de componentes

    REGLAS DE FORMATO Y REDACCIÓN (MUY IMPORTANTE):
    - NUNCA uses formato matemático ni LaTeX. ESTÁ TOTALMENTE PROHIBIDO encerrar texto o números entre signos de dólar ($ ... $).
    - Si vas a mencionar un valor monetario, debes "escapar" el signo de dólar usando una barra invertida (ejemplo: \$500.000) o usar la palabra "COP" (ejemplo: COP 500.000).
    - Usa negritas (**) solo para resaltar palabras clave completas, asegurándote de dejar espacios alrededor de los asteriscos. No pegues asteriscos a números o símbolos especiales.
    
    """    
    # Llamar a Gemini usando el "cliente" que creamos arriba
    respuesta = cliente.models.generate_content(
        # Usamos el nombre correcto del modelo para la nueva API
        model='gemini-flash-latest',
        contents=prompt_analisis
    )
    
    return respuesta.text
