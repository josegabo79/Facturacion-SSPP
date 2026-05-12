import streamlit as st
import pandas as pd
import json
import io
import base64
import plotly.express as px
import random
from chatbot_ia import consultar_chatbot
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 1. CONFIGURACIÓN DE PÁGINA Y DISEÑO (CSS)
st.set_page_config(page_title="Analista SSPP", page_icon="⚡", layout="wide")

# Solo dejamos la ruta del logo (Eliminamos RUTA_EXCEL porque ya usamos la nube)
RUTA_LOGO = r"C:\Users\JoseGabrielBlandonHe\OneDrive - Pactia\01 JEFATURA PY\2. Energia\Proyecto SSPP\Diseños\New Logo PACTIA.png"

#Estilos 
st.markdown("""
    <style>
        html, body, [class*="css"]  {
            font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        }
        .stSubheader { color: #374151; font-weight: 500 !important; border-bottom: 2px solid #E5E7EB; padding-bottom: 10px;
        }
        /* 1. Aumenta el ancho de los mensajes de la IA y del usuario */
        div[data-testid="stChatMessageContent"] { max-width: 1200px !important; }
        /* 2. Aumenta el ancho de la caja flotante donde escribes */
        div.stChatFloatingInputContainer { max-width: 1200px !important; }    
    </style>
    """, unsafe_allow_html=True)

estilos_sidebar = """
<style>
    /* Transforma los botones de radio en cajas redondeadas de IGUAL ANCHO */
    [data-testid="stSidebar"] div[role="radiogroup"] > label {
        background-color: #FFFFFF;
        border: 1.5px solid #E5E7EB;
        border-radius: 12px;
        padding: 12px 15px;
        margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.03);
        transition: all 0.3s ease;
        cursor: pointer;
        width: 100%; /* Fuerza a que ocupen todo el ancho disponible */
        display: flex; /* Mantiene el texto y el círculo bien alineados */
        box-sizing: border-box; /* Evita que el borde rompa el tamaño */
    }
    
    /* Efecto al pasar el mouse (hover) */
    [data-testid="stSidebar"] div[role="radiogroup"] > label:hover {
        border-color: #1E3A8A;
        background-color: #F8FAFC;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        transform: translateY(-1px);
    }
</style>
"""
st.markdown(estilos_sidebar, unsafe_allow_html=True)
#---------------------------------------------------------------------

# --- Función: NUEVA CONEXIÓN SEGURA A GOOGLE SHEETS DESDE LA NUBE ---
@st.cache_data(ttl=3600)
def cargar_datos():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        credenciales_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(credenciales_dict, scope)
        cliente_sheets = gspread.authorize(creds)
        
        hoja = cliente_sheets.open("Datos_SSPP").sheet1
        
        # Traemos los valores sin formato para que Google envíe números puros cuando pueda
        datos = hoja.get_all_records(value_render_option='UNFORMATTED_VALUE')
        df = pd.DataFrame(datos)
        
        # --- LIMPIEZA DE FILAS FANTASMAS ---
        df.replace("", pd.NA, inplace=True) 
        df.dropna(how="all", inplace=True) 
        df.dropna(axis=1, how="all", inplace=True)
        # Llenamos los vacíos con texto en blanco para no enviarle errores a la IA
        df.fillna("", inplace=True) 
        
        # --- LIMPIEZA INTELIGENTE DE NÚMEROS ---
        def limpiar_numero(x):
            if isinstance(x, str):
                x_limpio = x.replace(',', '.') # Reemplaza punto por coma #.replace('.', '') Para quitar puntos
                try:
                    return float(x_limpio)
                except ValueError:
                    return x # Si es texto real (ej. "Buró 51"), se queda igual
            return x # Si ya era un número puro desde Google, no lo tocamos

        # Aplicamos la limpieza a todas las columnas
        for col in df.columns:
            df[col] = df[col].apply(limpiar_numero)

        nombre_columna_fecha = 'Mes_pago'
        if nombre_columna_fecha in df.columns:        
            df[nombre_columna_fecha] = pd.to_datetime(          # 1. Convierte el número raro (45658) a una fecha real (ej. 2025-01-01)
                df[nombre_columna_fecha], 
                origin='1899-12-30', 
                unit='D', 
                errors='coerce' # Si hay celdas vacías, las ignora sin dar error
            )    
        # 2. Opcional pero Recomendado: Forzar a que de una vez quede como texto (Ej: "2025-01")
        # Para que la IA ya reciba un texto claro y no se confunda
        df[nombre_columna_fecha] = df[nombre_columna_fecha].dt.strftime('%Y-%m')


        return df
        
    except Exception as e:
        st.error(f"⚠️ Error al conectar con Google Sheets: {e}")
        return pd.DataFrame()

# --- FUNCIÓN MAESTRA DE GRÁFICAS ÚNICA Y CORREGIDA ---
def mostrar_mensaje_con_graficas(contenido):
    texto_principal = contenido
    datos_barra = []
    datos_torta = []

    # 1. Extracción del bloque JSON
    if "```json" in contenido:
        try:
            partes = contenido.split("```json")
            texto_principal = partes[0].strip()
            bloque_json = partes[1].split("```")[0].strip()
            
            diccionario_datos = json.loads(bloque_json)
            datos_barra = diccionario_datos.get("grafica_barra", [])
            datos_torta = diccionario_datos.get("grafica_torta", [])
        except Exception:            
            pass # Si falla el parseo, al menos mostramos el texto

    # 2. Renderizado del Texto de la IA
    st.markdown(texto_principal)

    # 3. Renderizado de Gráficas (Mismo diseño de columnas y estilos)
    if datos_barra or datos_torta:
        st.markdown("<br>", unsafe_allow_html=True)
        st.divider()       
                
        # Tu paleta de colores original
        tonos_estilo = ['#1C588C', '#2B678C', '#609BBF', '#84C1D9', '#99B8BF', '#94A3B8', '#8CBEB2', '#F2EBBF', '#F3B562', '#89D99D']
        colores_barras = random.sample(tonos_estilo, len(tonos_estilo))
        
        # Mantenemos tus proporciones de columna exactas
        col_barra, col_espacio, col_torta = st.columns([2.5, 0.3, 1.2]) 

        # --- GRÁFICA DE BARRAS ---
        if datos_barra:
            with col_barra:
                try:
                    df_bar = pd.DataFrame(datos_barra)
                    eje_x = df_bar.columns[0]
                    ejes_y = list(df_bar.columns[1:]) 

                    fig_bar = px.bar(df_bar, x=eje_x, y=ejes_y, barmode='group',
                                   title="Evolución Histórica", 
                                   labels={"variable": "Edificio", "value": "Total"},
                                   color_discrete_sequence=colores_barras)
                    fig_bar.update_layout(xaxis_type='category'  # Esto fuerza a Plotly a imprimir "Enero", "Febrero" y no números
                        )
                    
                    fig_bar.update_layout(
                        height=450, 
                        legend=dict(orientation="h", yanchor="top", y=-0.25, xanchor="center", x=0.5),
                        margin=dict(b=80)
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)
                except:
                    st.error("Error en formato de barras")

        # --- GRÁFICA DE TORTA ---
        if datos_torta:
            with col_torta:
                try:
                    df_pie = pd.DataFrame(datos_torta)
                    # Tomamos la primera columna como nombres y la segunda como valores
                    fig_pie = px.pie(df_pie, names=df_pie.columns[0], values=df_pie.columns[1],
                                   title="Distribución componentes CU", hole=0.4,
                                   color_discrete_sequence=px.colors.qualitative.Pastel)
                    
                    fig_pie.update_layout( 
                        # height=450, 
                        showlegend=True,
                        legend=dict(orientation="h", y=-0.2, xanchor="center", x=0.5),
                        margin=dict(l=20, r=20, t=30, b=20),
                        # margin=dict(b=80)
                    )
                    fig_pie.update_traces(textinfo='percent')
                    st.plotly_chart(fig_pie, use_container_width=True)
                except:
                    st.error("Error en formato de torta")

# --- SUGERENCIAS ---
SUGGESTIONS = {
    "🔌 Consumo Total": "Resume el consumo total de energía del último mes facturado sumando todos los edificios y compáralo con dos periodos anteriores.",
    "📊 Graficar Costo Unitario": "Genera una gráfica comparando el Costo Unitario (CU) de los diferentes edificios este mes.",
    "🏢 Edificio con mayor cobro": "¿Cuál fue el edificio o contrato que presentó el mayor valor a pagar en la última facturación? y compáralo con dos periodos anteriores",
    "⚠️ Detectar anomalías": "Analiza los datos y dime si existe algún cobro atípico o anomalía en los componentes (Generación, Comercialización, etc)."
}

# --- BANNER SUPERIOR ---
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        return ""

img_base64 = get_base64_image(RUTA_LOGO)
logo_html = f'<img src="data:image/png;base64,{img_base64}" style="height: 55px; margin-right: 25px;">' if img_base64 else ''

banner_html = f"""
<div style="background-color: #FFFFFF; padding: 15px 35px; border: 2px solid #E5E7EB; border-radius: 12px; margin-bottom: 25px; display: flex; align-items: center; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
    {logo_html}
    <h1 style="color: #1E3A8A; margin: 0; font-size: 28px; font-weight: bold; font-family: 'Segoe UI', sans-serif;">⚡ Plataforma Analítica SSPP</h1>
</div>
"""
st.markdown(banner_html, unsafe_allow_html=True)

# 1. Creamos el menú en la barra lateral
st.sidebar.markdown("<div style='height: 200px;'></div>", unsafe_allow_html=True) #Saltos de línea
st.sidebar.title("Navegación") 
opcion_elegida = st.sidebar.radio("Ir a:", ["📈 Dashboard Energía", "💡Asistente IA"])

# --- PESTAÑA 1: DASHBOARD ---
if opcion_elegida == "📈 Dashboard Energía":
    st.sidebar.markdown("<br><br><br>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: left; font-size: 32px; color: #1C588C; font-weight: 600;'>Dashboard de Energía</h3>", unsafe_allow_html=True)    
    st.markdown("<br>", unsafe_allow_html=True)
    #st.subheader("Tablero Interactivo de Energía")
    
    ENLACE_POWER_BI = "https://app.powerbi.com/reportEmbed?reportId=e58f7b05-80a4-4875-a0d8-fcbfb11d47ed&autoAuth=true&ctid=6503c5d1-70bc-437f-a0b6-a7849af8c68c&navContentPaneEnabled=false"
    
    iframe_responsivo = f"""
    <iframe title="Dashboard SSPP" 
            src="{ENLACE_POWER_BI}" 
            style="display: block; margin: 0 auto; width: 80%; height: 1200px; border: none;" 
            allowFullScreen="true">
    </iframe>
    """    
    st.markdown(iframe_responsivo, unsafe_allow_html=True)

# --- PESTAÑA 2: CHATBOT ---
elif opcion_elegida == "💡Asistente IA":
    st.markdown("<h3 style='text-align: left; font-size: 32px; color: #1C588C; font-weight: 600;'>Asistente de Inteligencia Artificial SSPP</h3>", unsafe_allow_html=True)
    col_vacia_izq, col_central, col_vacia_der = st.columns([1, 4, 1])

    with col_central:
        st.markdown("<br>", unsafe_allow_html=True)
        #st.subheader("Analista Virtual SSPP")        
        seleccion_pill = st.pills(
            "Sugerencias de análisis:", 
            options=list(SUGGESTIONS.keys()), 
            selection_mode="single",
            key="pills_input"
        )

        prompt_usuario = st.chat_input("Escribe tu duda sobre las facturas...")
        
        # Determina qué preguntar basándose en si hizo clic o si escribió
        prompt_final = None
        if prompt_usuario:
            prompt_final = prompt_usuario
        elif seleccion_pill:
            prompt_final = SUGGESTIONS[seleccion_pill]

        if prompt_final:
            with st.chat_message("user"):
                st.markdown(prompt_final)

            with st.chat_message("assistant"):
                with st.spinner("Analizando datos y generando gráficas..."):
                    try:
                        df = cargar_datos() 
                        
                        if not df.empty:
                            respuesta_ia = consultar_chatbot(prompt_final, df)
                            mostrar_mensaje_con_graficas(respuesta_ia)
                        else:
                            st.warning("⚠️ No se pudieron obtener datos de Google Sheets.")
                            
                    except Exception as e:
                        st.error(f"Error al procesar la consulta: {e}")
        else:
            st.info("👋 Bienvenido. Selecciona una sugerencia arriba o escribe tu consulta para analizar los datos de facturación.")