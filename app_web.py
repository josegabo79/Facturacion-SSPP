import streamlit as st
import pandas as pd
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
RUTA_LOGO = "New Logo PACTIA.png"

#Estilos 
st.markdown("""
    <style>
        html, body, [class*="css"]  {
            font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        }
        .stSubheader {
            color: #374151;
            font-weight: 600 !important;
            border-bottom: 2px solid #E5E7EB;
            padding-bottom: 10px;
        }
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
        
        # EL TRUCO ESTÁ AQUÍ: UNFORMATTED_VALUE trae el número puro en lugar del formato de texto
        datos = hoja.get_all_records(value_render_option='UNFORMATTED_VALUE')
        df = pd.DataFrame(datos)
        
        # --- LIMPIEZA DE FILAS FANTASMAS ---
        df.replace("", pd.NA, inplace=True) 
        df.dropna(how="all", inplace=True) 
        df.dropna(axis=1, how="all", inplace=True)
        
        # --- REDUNDANCIA DE COMAS A PUNTOS ---
        # Si quedó algún texto colado, lo convertimos forzosamente a decimal exacto
        for col in df.columns:
            if df[col].dtype == object:
                try:
                    df[col] = df[col].astype(str).str.replace(',', '.').astype(float)
                except ValueError:
                    pass # Si no es un número (ej. "Buró 51"), se queda como texto
                    
        return df
        
    except Exception as e:
        st.error(f"⚠️ Error al conectar con Google Sheets: {e}")
        return pd.DataFrame()

# --- FUNCIÓN MAESTRA DE GRÁFICAS ÚNICA Y CORREGIDA ---
def mostrar_mensaje_con_graficas(contenido):
    texto_principal = contenido
    datos_barra = None
    datos_torta = None

    # 1. Separación de los bloques exactos de la IA
    if "---GRAFICA_BARRA---" in texto_principal:
        partes = texto_principal.split("---GRAFICA_BARRA---")
        texto_principal = partes[0]
        resto = partes[1]
        
        if "---GRAFICA_TORTA---" in resto:
            partes_resto = resto.split("---GRAFICA_TORTA---")
            datos_barra = partes_resto[0].strip()
            datos_torta = partes_resto[1].strip()
        else:
            datos_barra = resto.strip()

    # 2. Mostramos el texto hablado de la IA
    st.markdown(texto_principal)

    # 3. Dibujar las gráficas si la IA mandó datos
    if datos_barra or datos_torta:
        st.markdown("<br>", unsafe_allow_html=True)
        st.divider()       
                
        tonos_estilo = [ 
            '#1C588C', '#2B678C', '#609BBF', '#84C1D9', '#99B8BF', 
            '#94A3B8', '#8CBEB2', '#F2EBBF', '#F3B562', '#89D99D' 
        ]
        
        colores_barras = random.sample(tonos_estilo, len(tonos_estilo))
        
        col_barra, col_espacio, col_torta = st.columns([2.5, 0.3, 1.2]) 

        # --- GRAFICAR BARRAS ---
        if datos_barra:
            with col_barra:
                try:
                    df_bar = pd.read_csv(io.StringIO(datos_barra), sep=",")
                    if not df_bar.empty:
                        eje_x = df_bar.columns[0]
                        ejes_y = list(df_bar.columns[1:]) 

                        fig_bar = px.bar(df_bar, x=eje_x, y=ejes_y, barmode='group',
                                       title="Evolución Histórica", labels={"variable": "Edificio ", "value": "Total " }, 
                                       color_discrete_sequence=colores_barras)
                        
                        fig_bar.update_layout(
                            height=450, 
                            xaxis_title=eje_x.capitalize(), 
                            yaxis_title="Valor",
                            legend_title_text='', 
                            legend=dict(orientation="h", yanchor="top", y=-0.25, xanchor="center", x=0.5),
                            margin=dict(b=80) 
                        )
                        st.plotly_chart(fig_bar, use_container_width=True)
                except Exception as e:
                    st.error(f"⚠️ Error renderizando barras: {e}")

        # --- GRAFICAR TORTA ---
        if datos_torta:
            with col_torta:
                try:
                    df_pie = pd.read_csv(io.StringIO(datos_torta), sep=",")
                    if not df_pie.empty:
                        fig_pie = px.pie(df_pie, names=df_pie.columns[0], values=df_pie.columns[1],
                                       title="Distribución componentes CU", hole=0.4,
                                       color_discrete_sequence=px.colors.qualitative.Pastel)
                        
                        fig_pie.update_layout(
                            height=450, # AQUÍ ESTABA EL ERROR DE LOS 3500px EN LA VERSIÓN VIEJA
                            showlegend=True,
                            legend=dict(orientation="h", yanchor="top", y=-0.25, xanchor="center", x=0.5),
                            margin=dict(b=80)
                        )
                        fig_pie.update_traces(textinfo='percent')
                        st.plotly_chart(fig_pie, use_container_width=True)
                except Exception as e:
                    st.error(f"⚠️ Error renderizando torta: {e}")

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
    st.title("Dashboard de Energía")
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
    st.title("Asistente de Inteligencia Artificial")
    col_vacia_izq, col_central, col_vacia_der = st.columns([1, 4, 1])

    with col_central:
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("Analista Virtual SSPP")
        
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
