import warnings
from google import genai

# Silenciar advertencias futuras de Pandas para mantener la consola limpia
warnings.simplefilter(action='ignore', category=FutureWarning)

# --- ESCUDO ANTI-ECO DE WINDOWS ---
archivos_procesados_memoria = set()

# --- RUTAS DE ARCHIVOS ---
ruta_excel = "https://pactia-my.sharepoint.com/:x:/p/jblandon/IQBByiYCKLQpT4JUOqcorATHAS7CasuVrB70SFxOeH4amVc?download=1"

carpetas_edificios = {
    "Buró 51": r"C:\Users\JoseGabrielBlandonHe\OneDrive - Pactia\01 JEFATURA PY\2. Energia\Proyecto SSPP\Facturas\Buro 51",
    "Buró 25 T2": r"C:\Users\JoseGabrielBlandonHe\OneDrive - Pactia\01 JEFATURA PY\2. Energia\Proyecto SSPP\Facturas\Buro 25 T2",
    "Buró 4.0": r"C:\Users\JoseGabrielBlandonHe\OneDrive - Pactia\01 JEFATURA PY\2. Energia\Proyecto SSPP\Facturas\Buro 4.0",
    "Buró 25 T3" : r"C:\Users\JoseGabrielBlandonHe\OneDrive - Pactia\01 JEFATURA PY\2. Energia\Proyecto SSPP\Facturas\Buro 25 T3",
    "Buró 24" : r"C:\Users\JoseGabrielBlandonHe\OneDrive - Pactia\01 JEFATURA PY\2. Energia\Proyecto SSPP\Facturas\Buro 24",
    "Buró 26" : r"C:\Users\JoseGabrielBlandonHe\OneDrive - Pactia\01 JEFATURA PY\2. Energia\Proyecto SSPP\Facturas\Buro 26"
}

# --- CONTROL DE INTERFAZ ---
MOSTRAR_RAZONAMIENTO_CONSOLA = False 

# --- CONFIGURACIÓN DE LLAVES DE API ---
API_KEYS = [
    "AIzaSyA1Q4UL8doXVBPUjmBmDoMBv0Ze7oJCJlc",
    "AIzaSyC1VZFhqkCcLpDFXuUQ10mwqnksCH8GJ3M"
]

indice_key_actual = 0
cliente = genai.Client(api_key=API_KEYS[indice_key_actual])

def rotar_api_key():
    """Esta función cambia a la siguiente API Key en la lista cuando la actual se satura."""
    global indice_key_actual, cliente
    indice_key_actual = (indice_key_actual + 1) % len(API_KEYS)
    print(f"🔄 Rotando a la API Key #{indice_key_actual + 1}...")
    cliente = genai.Client(api_key=API_KEYS[indice_key_actual])
