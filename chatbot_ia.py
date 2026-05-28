import pandas as pd
from google import genai
import streamlit as st
import time
import psycopg2 # Asegúrate de que esta librería esté importada arriba

# --- CONEXIÓN SEGURA EN LA NUBE PARA GEMINI ---  
try:
    # El código va a la caja fuerte de Streamlit y saca la llave llamada "GEMINI_API_KEY"
    llave_secreta = st.secrets["GEMINI_API_KEY"]
    cliente_ia = genai.Client(api_key=llave_secreta)
except Exception as e:
    st.error("⚠️ Error de seguridad: No se encontró la llave de Gemini en los Secretos.")
    
    cliente_ia = None

# --- ESTRUCTURA DE LA BASE DE DATOS PARA LA IA ---
TABLA_NOMBRE = "facturas_energia"
COLUMNAS_DB = """
comercializador, contrato, nivel_tension, mes_pago, cu_total, consumo_total, 
subtotal_generacion, subtotal_transporte_nac, subtotal_transporte_reg, subtotal_distribucion, 
subtotal_comercializacion, subtotal_perdidas, subtotal_restricciones, total_pagar, subtotal, 
energia_reactiva, valor_aseo, valor_seguridad, alumbrado_publico, cobros_atipicos, 
cu_generacion, cu_comercializacion, cu_perdidas, cu_transporte_nacional, cu_transporte_regional, 
cu_distribucion, cu_restricciones, edificio, archivo_origen
"""
def ejecutar_sql_en_supabase(query_sql):
    """Función para conectar al motor PostgreSQL de Supabase y ejecutar el SQL localmente"""
    try:
        # Tomamos las credenciales de tu secrets.toml
        conexion = psycopg2.connect(
            host=st.secrets["DB_HOST"],
            database=st.secrets["DB_NAME"],
            user=st.secrets["DB_USER"],
            password=st.secrets["DB_PASSWORD"],
            port=st.secrets["DB_PORT"]
        )
        # Ejecutamos la consulta y la convertimos en un DataFrame instantáneo
        df_resultado = pd.read_sql_query(query_sql, conexion)
        conexion.close()
        return df_resultado
    
    except Exception as e:
        return f"Error ejecutando SQL: {e}"

# NOTA: Ya no le pasamos el 'dataframe' pesado a esta función, solo la 'pregunta'
def consultar_chatbot(pregunta):
    if not cliente_ia:
        return "⚠️ Error: Cliente de IA no configurado."
        
    # =========================================================================
    # PASO A: TRADUCCIÓN DE LENGUAJE NATURAL A SQL
    # =========================================================================
    prompt_sql = f"""
    Eres un analista de datos experto en bases de datos PostgreSQL.
    Tu única tarea es traducir la pregunta del usuario en una consulta SQL válida.
    
    ESTRUCTURA DE LA BASE DE DATOS:
    - Tabla: {TABLA_NOMBRE}
    - Columnas: {COLUMNAS_DB}
    
    REGLAS ESTRICTAS:
    1. Devuelve ÚNICAMENTE el código SQL puro. Nada de saludos, ni explicaciones, ni etiquetas de código Markdown (```sql ... ```). No añadas punto y coma al final.
    2. Usa la función ILIKE para búsquedas de texto ignorando mayúsculas/minúsculas (ej: edificio ILIKE '%Buró 51%').
    3. Asegúrate de seleccionar solo las columnas necesarias para responder a la pregunta.
    
    PREGUNTA DEL USUARIO: {pregunta}
    """
    
    try:
        # Pedir a Gemini que genere el SQL (Gasto ínfimo de tokens)
        respuesta_sql = cliente_ia.models.generate_content(
            model='gemini-3.1-flash-lite', # o 'gemini-flash-latest' según la versión que prefieras
            contents=prompt_sql
        )
        
        # Limpiamos el texto por si la IA añade etiquetas Markdown por error
        query_generada = respuesta_sql.text.replace("```sql", "").replace("```", "").strip()        
        
        # =========================================================================
        # PASO B: EJECUCIÓN LOCAL EN SUPABASE
        # =========================================================================
        resultado_db = ejecutar_sql_en_supabase(query_generada)
        
        # Validación de errores
        if isinstance(resultado_db, str) and "Error" in resultado_db:
             return f"⚠️ Hubo un error al consultar la base de datos: {resultado_db}"
             
        if resultado_db.empty:
            return "Lo siento, no encontré registros en la base de datos que coincidan con tu pregunta."
            
        # Convertimos la respuesta exacta en un texto ligero
        datos_para_ia = resultado_db.to_dict(orient='records')
        
        # =========================================================================
        # PASO C: GENERAR RESPUESTA FINAL (TEXTO + GRÁFICAS)
        # =========================================================================
        prompt_final = f"""
        Eres el asistente inteligente del "Proyecto Facturación SSPP".
        El usuario te hizo esta pregunta: "{pregunta}"
        
        Tu sistema de base de datos extrajo exactamente estos resultados:
        {datos_para_ia}
        
        TU TAREA:
        1. Responde a la pregunta de forma amigable, clara y profesional basándote SOLO en esos datos.
        2. SIEMPRE debes terminar la respuesta con UN ÚNICO bloque ```json válido y parseable.  
        3. NO escribas texto después del JSON.
        4. El JSON debe ser válido para json.loads() de Python.
        5. Los valores numéricos NO deben ir entre comillas.
        6. La columna oficial para fechas es mes_pago tipo DATE, representa fechas mensuales y debe usarse para ordenar cronológicamente DESCENDENTE. 
        7. SIEMPRE tomar los meses más recientes disponibles en la base de datos, consecutivos reales. Usar SIEMPRE ORDER BY mes_pago 
        8. Traer los datos de los meses que pida el usuario o si no pide nada traer 4 ulimos meses.      

        9. Grafico Barra:   
        - MODO SERIES (Comparativa total): Si piden comparar o ver todos los edificios, usa múltiples columnas incluyendo TODOS los edificios. 
        - Traer los datos que pida el usuario para El Valor en las series: consumo (columna: Consumo_Total), costo o gasto en pesos (Columna: valor) (Columna: "Subtotal") o CU (Columna: CU_Total). Si no pide consumo o CU, traer datos del costo.
        - REGLA CRÍTICA: PROHIBIDO RESUMIR. NO uses "etc". El JSON debe contener las columnas de TODOS los edificios sin omitir ninguno. Si la tabla de tu respuesta tiene 6 edificios, el JSON debe tener las 6 columnas de esos edificios.
        
        10. Gráfico torta:
        Pon el promedio de los 6 componentes exactos: Generación (CU_Generación), Transmisión (CU_Transporte_Nacional), Distribución (CU_Distribucion + CU_Transporte_Regional), Comercialización (CU_Comercializacion), Restricciones (CU_Restricciones), Pérdidas (CU_Perdidas). 
        Si preguntan por un solo edificio y no tiene componentes poner el valor de Costo Unitario (CU_Total)  y no poner columnas de componentes

        11. El formato de grafica_barra debe ser compatible con Plotly Express usando:px.bar(df, x="Mes", y=[lista_de_edificios])

        12. El bloque JSON debe tener EXACTAMENTE esta estructura:
        
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

        REGLA CRÍTICA:
        - grafica_torta SIEMPRE debe contener al menos una fila.
        - Nunca devuelvas arrays vacíos.
        - Si pregunta por varios edificios sacar el promedio de componnetes de todos y traer esos datos
        - Si no existen los 6 componentes exactos CU_* usa:
        [
        {{"Categoria":"CU_Total","Value":123.45}}
        ]       

        """
        
        respuesta_final = cliente_ia.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt_final
        )
        
        return respuesta_final.text
        
    except Exception as e:
        return f"⚠️ Ocurrió un error general al procesar tu solicitud: {e}"