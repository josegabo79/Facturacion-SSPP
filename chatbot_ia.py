import pandas as pd
from google import genai
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
    
    # 1. Definimos SOLO las columnas que la IA realmente necesita para analizar y graficar.
    # (Ajusta estos nombres exactos según cómo se llamen en tu Google Sheets)
    columnas_esenciales = [
        "Comercializador", "Edificio", "Mes_pago", "Consumo_Total", "Total_Pagar", "Subtotal","Energia_reactiva", "CU_Total", 
        "CU_Generacion", "CU_Comercializacion", "CU_Perdidas", 
        "CU_Transporte_Nacional", "CU_Transporte_Regional", "CU_Distribucion", "CU_Restricciones",
        "Cobros_Atipicos"
    ]

    # 2. Filtramos el dataframe para que cruce solo las columnas que existen
    columnas_filtradas = [col for col in columnas_esenciales if col in dataframe.columns]
    df_ligero = dataframe[columnas_filtradas]    
    
    datos_completos = df_ligero.to_csv(index=False) # Convertimos a CSV exacto para no saturar a la IA ni demorarla con espacios
    
    prompt_analisis = f"""
    Eres el Analista Senior de Energía de Pactia. 
    Tu base de datos es la siguiente tabla de facturas procesadas en formato CSV:
    
    {datos_completos}
    
    Pregunta del usuario: {pregunta}
    
    REGLAS DE FORMATO Y REDACCIÓN (MUY IMPORTANTE):
    - Responde de forma clara, técnica. No traer tablas, solo el analisis de texto.
    - Si detectas valores de Energía Reactiva altos (mayores de 300.000) o penalidades, resáltalos.
    - Si comparas sedes, menciona el nombre de la sede exacto.
    - Nota: Los nombres de los edificios pueden variar la forma de escribirlos. Si la tabla de tu respuesta tiene 6 edificios, el CSV debe tener las 6 columnas de esos edificios.
    
    - NUNCA uses formato matemático ni LaTeX. ESTÁ TOTALMENTE PROHIBIDO encerrar texto o números entre signos de dólar ($ ... $).
    - Si vas a mencionar un valor monetario, debes "escapar" el signo de dólar usando una barra invertida (ejemplo: \\$500.000) o usar la palabra "COP" (ejemplo: COP 500.000).
    - Usa negritas (**) solo para resaltar palabras clave completas, asegurándote de dejar espacios alrededor de los asteriscos. No pegues asteriscos a números o símbolos especiales.
    - REGLA PARA FECHAS Y MESES: En los datos JSON, NUNCA uses números opara representar los meses. Usa SIEMPRE el fornato mm/aa (mes/año) (Ejemplo: "01/26" o "Feb/26").
    - Los valores numéricos deben ser números puros (Float/Int), NO textos entre comillas.
    
    Instrucciones finales:
    - Al final de tu respuesta, incluye SIEMPRE los datos para las gráficas en un bloque de código JSON con esta estructura exacta:
    Grafico Barra:
    - La Columna 1 SIEMPRE debe ser "Mes" (columna Mes_pago) (orden cronológico).    
    - Traer los datos de los meses que pida el usuario o si no pide nada traer 4 ulimos meses.  
    - MODO SERIES (Comparativa total): Si piden comparar o ver todos los edificios, usa múltiples columnas incluyendo TODOS los edificios. 
    - Traer los datos que pida el usuario para El Valor en las series: consumo (columna: Consumo_Total), costo o gasto en pesos (Columna: valor) (Columna: "Subtotal") o CU (Columna: CU_Total). Si no pide consumo o CU, traer datos del costo.
    - REGLA CRÍTICA: PROHIBIDO RESUMIR. NO uses "etc". El JSON debe contener las columnas de TODOS los edificios sin omitir ninguno. Si la tabla de tu respuesta tiene 6 edificios, el JSON debe tener las 6 columnas de esos edificios.
    Gráfico torta:
    Pon el promedio de los 6 componentes exactos: Generación (CU_Generación), Transmisión (Cu_Transmisión), Distribución (CU_Transporte_Nacional + CU_Transporte_Regional), Comercialización (CU_Comercializacion), Restricciones (CU_Restricciones), Pérdidas (CU_Perdidas). 
    Si preguntan por un solo edificio y no tiene componentes poner el valor de Costo Unitario (CU_Total)  y no poner columnas de componentes
    
    ```json
    {{
      "grafica_barra": [
        {{"Mes": "Enero", "Buró 51": 15000.50, "Buró 4.0": 20000.00}},
        {{"Mes": "Febrero", "Buró 51": 18000.00, "Buró 4.0": 22000.00}}
      ],
      "grafica_torta": [
        {{"Categoria": "Generación", "Value": 2681585.00}},
        {{"Categoria": "Distribución", "Value": 445835.00}}
      ]
    }}
    ```       
    """    

    # --- SISTEMA ANTICAÍDAS Y TOLERANCIA AL TRÁFICO (REINTENTOS AUTOMÁTICOS) ---
    max_reintentos = 3 
    
    for intento in range(max_reintentos):
        try:
            respuesta = cliente_ia.models.generate_content(
                model='gemini-flash-latest',                  # gemini-flash-latest, gemini-flash-lite-latest, gemini-2.5-pro
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
            return f"⚠️ Los servidores de IA están demasiado saturados analizando la base de datos en este momento. Por favor, intenta de nuevo en unos segundos. (Detalle técnico: {error_msg})"
        
        
""" REGLAS ESTRICTAS PARA GENERAR GRÁFICAS:
    SIEMPRE debes incluir DOS bloques al final de tu respuesta EXACTAMENTE con esta estructura:

    1. DEBES escribir la etiqueta ---GRAFICA_BARRA--- seguida de un salto de línea y un JSON estructurado dentro de un bloque de código. No uses etiquetas antiguas de CSV evolución en el tiempo:
    - La Columna 1 SIEMPRE debe ser "Mes" (columna Mes_pago) (orden cronológico).
    - Traer los datos de los meses que pida el usuario o si no pide nada traer 4 ulimos meses.  
    - MODO SERIES (Comparativa total): Si piden comparar o ver todos los edificios, usa múltiples columnas incluyendo TODOS los edificios. 
    - Traer los datos que pida el usuario para El Valor en las series: consumo (columna Consumo_Total), costo (valor) (Columna "Subtotal") o CU (Columna CU_Total). Si no pide consumo o CU, traer datos del costo.
    - REGLA CRÍTICA: PROHIBIDO RESUMIR. NO uses "etc". El JSON debe contener las columnas de TODOS los edificios sin omitir ninguno. Si la tabla de tu respuesta tiene 6 edificios, el JSON debe tener las 6 columnas de esos edificios.

    2. DEBES escribir la etiqueta ---GRAFICA_TORTA--- seguida de un salto de línea y un JSON estructurado dentro de un bloque de código. No uses etiquetas antiguas de CSV evolución en el tiempo:
    Categoria,Valor
    Pon el promedio de los 6 componentes exactos: Generación (CU_Generación), Transmisión (Cu_Transmisión), Distribución (CU_Transporte_Nacional + CU_Transporte_Regional), Comercialización (CU_Comercializacion), Restricciones (CU_Restricciones), Pérdidas (CU_Perdidas). 
    Si preguntan por un solo edificio y no tiene componentes poner el valor de Costo Unitario (CU_Total)  y no poner columnas de componentes
     """