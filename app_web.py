import streamlit as st
import pandas as pd
import json
import base64
import plotly.express as px
import random
from chatbot_ia import consultar_chatbot
import re

# 1. CONFIGURACIÓN DE PÁGINA Y DISEÑO (CSS)
st.set_page_config(page_title="Analista SSPP", page_icon="⚡", layout="wide")

#  RESPONSIVE CSS
st.markdown("""
<style>

.block-container {
    padding-top: 1.5rem;
    padding-bottom: 1rem;
    max-width: 100%;
}

/* SOLO afecta las gráficas */
.grafica-responsive {
    width: 100%;
}

</style>
""", unsafe_allow_html=True)

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
        div[data-testid="stChatMessageContent"] { max-width: 95vw !important;}
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

# --- FUNCIÓN MAESTRA DE GRÁFICAS ÚNICA Y CORREGIDA ---
def mostrar_mensaje_con_graficas(contenido):
    texto_principal = contenido
    datos_barra = []
    datos_torta = []

    # 1. Extracción del bloque JSON
    match = re.search(r"```json\s*(\{.*?\})\s*```", contenido, re.DOTALL)
    if match:
        try:
            bloque_json = match.group(1)
            diccionario_datos = json.loads(bloque_json)

            # st.json(diccionario_datos)      # Para ver lo que esta trayendo la IA --- temporal y luego quitar

            datos_barra = diccionario_datos.get("grafica_barra", [])
            datos_torta = diccionario_datos.get("grafica_torta", [])

            texto_principal = re.sub(
                r"```json\s*\{.*?\}\s*```",
                "",
                contenido,
                flags=re.DOTALL
            ).strip()

        except Exception as e:
            st.error(f"JSON inválido: {e}")        
    # --------------------------------------------------------------------

    # 2. Renderizado del Texto de la IA
    st.markdown(texto_principal)

    # 3. Renderizado de Gráficas (Mismo diseño de columnas y estilos)
    if datos_barra or datos_torta:
        st.markdown("<br>", unsafe_allow_html=True)
        st.divider()       
                
        # Tu paleta de colores original
        tonos_estilo = ['#1C588C', '#2B678C', '#609BBF', '#84C1D9', '#99B8BF', '#94A3B8', '#8CBEB2', '#F2EBBF', '#F3B562', '#89D99D']
        colores_barras = random.sample(tonos_estilo, len(tonos_estilo))

        # --- GRÁFICA DE BARRAS ---
        if datos_barra:
            with st.container():
                try:
                    df_bar = pd.DataFrame(datos_barra)

                    eje_x = df_bar.columns[0]
                    ejes_y = list(df_bar.columns[1:])

                    fig_bar = px.bar(
                        df_bar,
                        x=eje_x,
                        y=ejes_y,
                        barmode='group',
                        title="<b>Evolución Histórica</b>",
                        labels={
                            "variable": "Edificio",
                            "value": "Total"
                        },
                        color_discrete_sequence=colores_barras,
                        opacity=0.92
                    )

                    fig_bar.update_layout(
                        height= 500,
                        autosize=True,

                        margin=dict(
                            l=20,
                            r=20,
                            t=50,
                            b=80
                        ),
                        legend=dict(
                            orientation="h",
                            yanchor="top",
                            y=-0.25,
                            xanchor="center",
                            x=0.5
                        ),
                        xaxis=dict(
                            type='category',
                            tickangle=-35
                        ),
                        title=dict(
                        x=0.5,xanchor='center'
                        ),
                    )

                    st.plotly_chart(
                        fig_bar,
                        use_container_width=True
                    )

                    st.markdown("<br><br>", unsafe_allow_html=True) # Espacio vertical entre gráficos

                except Exception as e:
                    st.error(f"Error en gráfica barras: {e}")

        # --- GRÁFICA DE TORTA ---
        if datos_torta:
            with st.container():
                try:
                    df_pie = pd.DataFrame(datos_torta)

                    if (
                        "Categoria" in df_pie.columns and
                        "Value" in df_pie.columns
                    ):

                        fig_pie = px.pie(
                            df_pie,
                            names="Categoria",
                            values="Value",
                            hole=0.62,
                            title="<b>Distribución Componentes CU</b>"                 
                        )
                        fig_pie.update_layout(
                            showlegend=True,
                            height= 500,
                            autosize=True,

                            margin=dict(
                                l=10,
                                r=10,
                                t=50,
                                b=10
                            ),
                            
                            legend=dict(
                                orientation="h",
                                yanchor="top",
                                y=-0.15,
                                xanchor="center",
                                x=0.5
                            ),

                            title=dict(
                            x=0.5,
                            xanchor='center'
                            ),
                            uniformtext_minsize=10,
                            uniformtext_mode='hide'                            
                        )

                        fig_pie.update_traces(
                            textinfo='percent',
                            textposition='auto'
                        )

                        st.plotly_chart(
                            fig_pie,
                            use_container_width=True
                        )

                    else:
                        st.warning(
                            "Formato inválido para gráfica torta"
                        )

                except Exception as e:
                    st.error(f"Error torta: {e}")                  

# --- SUGERENCIAS ---
SUGGESTIONS = {
    "🔌 Consumo Total": "Analiza el consumo total de energía del último mes facturado para cada uno de los edificios y compáralo con dos periodos anteriores.",
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
                        respuesta_ia = consultar_chatbot(prompt_final)
                        mostrar_mensaje_con_graficas(respuesta_ia)
                            
                    except Exception as e:
                        st.error(f"Error al procesar la consulta: {e}")
        else:
            st.info("👋 Bienvenido. Selecciona una sugerencia arriba o escribe tu consulta para analizar los datos de facturación.")