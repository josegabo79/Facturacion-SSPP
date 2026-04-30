import streamlit as st
import pandas as pd
import io
import base64
import streamlit.components.v1 as components
from extractor_ia import consultar_chatbot

# 1. CONFIGURACIÓN DE PÁGINA Y DISEÑO (CSS)
st.set_page_config(page_title="Analista SSPP", page_icon="⚡", layout="wide")

# Rutas de tus archivos locales (Verifica que la del logo sea correcta)
RUTA_EXCEL = "https://pactia-my.sharepoint.com/:x:/p/jblandon/IQBByiYCKLQpT4JUOqcorATHAQypG55Iqy2rQzidfCA32zU?download=1"
RUTA_LOGO = "New Logo PACTIA.png"

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

# 2. EL BANNER SUPERIOR (Fondo Blanco, Borde Gris y Logo Tabulado)
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        return ""

img_base64 = get_base64_image(RUTA_LOGO)
# Añadimos un poco más de margen derecho al logo para separarlo del texto
logo_html = f'<img src="data:image/png;base64,{img_base64}" style="height: 55px; margin-right: 25px;">' if img_base64 else ''

# Banner con fondo blanco, borde gris, padding ampliado (tabulado) y título con el rayo en azul
banner_html = f"""
<div style="background-color: #FFFFFF; padding: 15px 35px; border: 2px solid #E5E7EB; border-radius: 12px; margin-bottom: 25px; display: flex; align-items: center; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
    {logo_html}
    <h1 style="color: #1E3A8A; margin: 0; font-size: 28px; font-weight: bold; font-family: 'Segoe UI', sans-serif;">⚡ Plataforma Analítica SSPP</h1>
</div>
"""
st.markdown(banner_html, unsafe_allow_html=True)

# 3. CREACIÓN DE PESTAÑAS
tab_dashboard, tab_chat = st.tabs(["📊 Dashboard de Consumos", "🤖 Analista Virtual"])

# --- PESTAÑA 1: DASHBOARD ---
with tab_dashboard:
    st.markdown("<br>", unsafe_allow_html=True)
    
    ENLACE_POWER_BI = "https://app.powerbi.com/reportEmbed?reportId=e58f7b05-80a4-4875-a0d8-fcbfb11d47ed&autoAuth=true&ctid=6503c5d1-70bc-437f-a0b6-a7849af8c68c&navContentPaneEnabled=false"
    
    # Dashboard Centrado
    st.markdown(
        f"""
        <div align="center">
            <iframe title="Power BI Dashboard" width="1200" height="1000" 
            src="{ENLACE_POWER_BI}" frameborder="0" allowFullScreen="true"></iframe>
        </div>
        """,
        unsafe_allow_html=True
    )

# --- PESTAÑA 2: CHATBOT ---
with tab_chat:
    st.subheader("Consultas Inteligentes")
    
    try:
        df = pd.read_excel(RUTA_EXCEL)

        if "messages" not in st.session_state:
            st.session_state.messages = []

        chat_container = st.container()

        with chat_container:
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    if msg["role"] == "assistant" and "---GRAFICA---" in msg["content"]:
                        partes = msg["content"].split("---GRAFICA---")
                        st.markdown(partes[0])
                        try:
                            df_plot = pd.read_csv(io.StringIO(partes[1].strip()), sep=",|;", engine="python")
                            st.bar_chart(data=df_plot, x=df_plot.columns[0], y=df_plot.columns[1])
                        except: pass
                    else:
                        st.markdown(msg["content"])

        if prompt := st.chat_input("Ej: ¿Cuál fue el edificio con mayor consumo el mes pasado?"):
            
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Analizando información..."):
                    respuesta = consultar_chatbot(prompt, df)
                    
                    if "---GRAFICA---" in respuesta:
                        partes = respuesta.split("---GRAFICA---")
                        st.markdown(partes[0])
                        try:
                            df_plot = pd.read_csv(io.StringIO(partes[1].strip()), sep=",|;", engine="python")
                            st.bar_chart(data=df_plot, x=df_plot.columns[0], y=df_plot.columns[1])
                        except:
                            st.warning("No pude generar la gráfica.")
                    else:
                        st.markdown(respuesta)
            
            st.session_state.messages.append({"role": "assistant", "content": respuesta})

    except Exception as e:
        st.error(f"⚠️ Error al conectar con la base de datos: {e}")
