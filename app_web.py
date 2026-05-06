import streamlit as st
import pandas as pd
import io
import base64
import streamlit.components.v1 as components
import plotly.express as px
import random
from chatbot_ia import consultar_chatbot

# Función para gráficar:

def mostrar_mensaje_con_graficas(contenido):
    # Variables iniciales
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

    # 3. Dibujar las gráficas
    if datos_barra or datos_torta:
        st.markdown("<br>", unsafe_allow_html=True)
        st.divider()       
                
        tonos_estilo = [ # 1. Defines tus tonos específicos (Ejemplo: Gama de azules corporativos y grises)   
            '#1C588C', # Tu azul principal
            '#2B678C', '#609BBF', '#84C1D9', '#99B8BF', '#94A3B8', 
            '#8CBEB2', '#F2EBBF', '#F3B562', '#89D99D' 
        ]
        
        # 2. Haces que se mezclen aleatoriamente en cada consulta. Así siempre usará tus colores, pero en distinto orden        
        colores_barras = random.sample(tonos_estilo, len(tonos_estilo))
        colores_torta = random.sample(tonos_estilo, len(tonos_estilo))
        # ---------------------------------

        col_barra, col_espacio, col_torta = st.columns([2.5, 0.3, 1.2]) # Espacios entre gráficas [2.5 (Barras), 0.3 (Espacio vacío), 1.2 (Torta)]

        # --- GRAFICAR BARRAS ---
        if datos_barra:
            with col_barra:
                try:
                    df_bar = pd.read_csv(io.StringIO(datos_barra), sep=",")
                    if not df_bar.empty:
                        eje_x = df_bar.columns[0]
                        ejes_y = list(df_bar.columns[1:]) 

                        fig_bar = px.bar(df_bar, x=eje_x, y=ejes_y, barmode='group',
                                       title="Evolución Histórica", labels={"variable": "Edificio ", "value": "Total " }, color_discrete_sequence=colores_barras)
                        
                        fig_bar.update_layout(
                            height=450, # Le damos un poco más de altura para que quepa la leyenda
                            xaxis_title=eje_x.capitalize(), 
                            yaxis_title="Valor",
                            legend_title_text='', # Quitamos el título de la leyenda para mayor limpieza
                            legend=dict(
                                orientation="h", # Horizontal
                                yanchor="top",
                                y=-0.25, # La empujamos hacia abajo
                                xanchor="center",
                                x=0.5
                            ),
                            margin=dict(b=80) # Margen inferior extra para que no se corte el texto
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
                                       labels={"Categoría": "Componente ", "value": "Total " },
                                       color_discrete_sequence=px.colors.qualitative.Pastel)
                        
                        fig_pie.update_layout(
                            height=450, 
                            showlegend=True,
                            legend=dict(
                                orientation="h",
                                yanchor="top",
                                y=-0.25,
                                xanchor="center",
                                x=0.5
                            ),
                            margin=dict(b=80)
                        )
                        fig_pie.update_traces(textinfo='percent')
                        st.plotly_chart(fig_pie, use_container_width=True)
                except Exception as e:
                    st.error(f"⚠️ Error renderizando torta: {e}")

# -----------------------------------

# Sugerencias adaptadas al Proyecto Facturación SSPP (¡Mucho más útiles para tu equipo!)
SUGGESTIONS = {
    "💡 Consumo Total": (
        "Resume el consumo total de energía del último mes facturado sumando todos los edificios y compáralo con dos periodos anteriores."
    ),
    "📊 Graficar Costo Unitario": (
        "Genera una gráfica comparando el Costo Unitario (CU) de los diferentes edificios este mes."
    ),
    "🏢 Edificio con mayor cobro": (
        "¿Cuál fue el edificio o contrato que presentó el mayor valor a pagar en la última facturación? y compáralo con dos periodos anteriores"
    ),
    "⚠️ Detectar anomalías": (
        "Analiza los datos y dime si existe algún cobro atípico o anomalía en los componentes (Generación, Comercialización, etc)."
    ),
}

# 1. CONFIGURACIÓN DE PÁGINA Y DISEÑO (CSS)
st.set_page_config(page_title="Analista SSPP", page_icon="⚡", layout="wide")

# Rutas de tus archivos locales
RUTA_EXCEL = r"C:\Users\JoseGabrielBlandonHe\OneDrive - Pactia\01 JEFATURA PY\2. Energia\Proyecto SSPP\Datos_SSPP.xlsx"
RUTA_LOGO = r"C:\Users\JoseGabrielBlandonHe\OneDrive - Pactia\01 JEFATURA PY\2. Energia\Proyecto SSPP\Diseños\New Logo PACTIA.png"

# Inyectamos diseño corporativo para la tipografía general
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

# 2. EL BANNER SUPERIOR
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

# 3. CREACIÓN DE PESTAÑAS
tab_dashboard, tab_chat = st.tabs(["📈 Dashboard de Consumos", "🖥️ Analista Virtual"])

# --- PESTAÑA 1: DASHBOARD ---
with tab_dashboard:
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("Tablero Interactivo de Energía")
    
    ENLACE_POWER_BI = "https://app.powerbi.com/reportEmbed?reportId=e58f7b05-80a4-4875-a0d8-fcbfb11d47ed&autoAuth=true&ctid=6503c5d1-70bc-437f-a0b6-a7849af8c68c&navContentPaneEnabled=false"
    
    iframe_responsivo = f"""
    <iframe title="Dashboard SSPP" 
            src="{ENLACE_POWER_BI}" 
            style="display: block; margin: 0 auto; width: 80%; height: 1200px; border: none;" 
            allowFullScreen="true">
    </iframe>
    """    
    st.markdown(iframe_responsivo, unsafe_allow_html=True)

# --- PESTAÑA 2: CHATBOT (Versión Limpia sin Historial) ---
with tab_chat:
    col_vacia_izq, col_central, col_vacia_der = st.columns([1, 4, 1])

    with col_central:
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("Analista Virtual SSPP")
        
        # 1. Lógica de Sugerencias (Pills)
        # Usamos una clave única para que Streamlit detecte el cambio
        seleccion_pill = st.pills(
            "Sugerencias de análisis:", 
            options=list(SUGGESTIONS.keys()), 
            selection_mode="single",
            key="pills_input"
        )

        # Determinar el prompt final (o de la caja de texto o de la sugerencia)
        prompt_usuario = st.chat_input("Escribe tu duda sobre las facturas...")
        
        # Si se selecciona una sugerencia, esa es nuestra pregunta
        if seleccion_pill:
            prompt_final = SUGGESTIONS[seleccion_pill]
        else:
            prompt_final = prompt_usuario

        # 2. PROCESAMIENTO Y RENDERIZADO ÚNICO
        if prompt_final:
            # Mostramos la pregunta actual
            with st.chat_message("user"):
                st.markdown(prompt_final)

            # Generamos la respuesta
            with st.chat_message("assistant"):
                with st.spinner("Analizando datos y generando gráficas..."):
                    try:
                        # Cargamos el DF si no está cargado
                        df = pd.read_excel(RUTA_EXCEL)
                        # Llamada a tu función de IA
                        respuesta_ia = consultar_chatbot(prompt_final, df)
                        
                        # Mostramos el resultado con la función maestra
                        mostrar_mensaje_con_graficas(respuesta_ia)
                    except Exception as e:
                        st.error(f"Error al conectar con la base de datos: {e}")

        else:
            # Si no hay pregunta, mostramos un mensaje de bienvenida sutil
            st.info("👋 Bienvenido. Selecciona una sugerencia arriba o escribe tu consulta para analizar los datos de facturación.")

# --- AJUSTE EN LA FUNCIÓN MAESTRA PARA COMPONENTES ---
def mostrar_mensaje_con_graficas(contenido):
    if "---GRAFICA---" in contenido:
        partes = contenido.split("---GRAFICA---")
        st.markdown(partes[0]) 
        
        try:
            df_plot = pd.read_csv(io.StringIO(partes[1].strip()), sep=",|;", engine="python")
            
            if not df_plot.empty:
                st.markdown("<br>", unsafe_allow_html=True)
                st.divider()
                
                col_barra, col_torta = st.columns([2, 1])
                
                with col_barra:
                    # Barras para tendencia o comparación
                    fig_bar = px.bar(df_plot, x=df_plot.columns[0], y=df_plot.columns[1],
                                   title="Análisis de Valores",
                                   color_discrete_sequence=['#00529B'], text_auto='.2f')
                    fig_bar.update_layout(height=400)
                    st.plotly_chart(fig_bar, use_container_width=True)

                with col_torta:
                    # Torta para distribución (Componentes CU)
                    # Forzamos a que use la primera columna como etiquetas de componentes
                    fig_pie = px.pie(df_plot, names=df_plot.columns[0], values=df_plot.columns[1],
                                   title="Distribución de Costos", hole=0.4,
                                   color_discrete_sequence=px.colors.qualitative.Pastel)
                    fig_pie.update_layout(height=3500, showlegend=True) # Activamos leyenda para ver nombres de componentes
                    fig_pie.update_traces(textinfo='percent')
                    st.plotly_chart(fig_pie, use_container_width=True)
        except Exception as e:
            st.error(f"⚠️ Los datos de la gráfica no tienen el formato correcto.")
    else:
        st.markdown(contenido)