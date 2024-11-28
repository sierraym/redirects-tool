import streamlit as st
import pandas as pd
from urllib.parse import urlparse
from difflib import SequenceMatcher
from io import BytesIO
import re

# Lista de idiomas disponibles en la nueva web
available_languages = ['/', '/en/', '/de/']  # Agrega o elimina idiomas según corresponda

# Mapeo de idiomas a sus respectivas páginas de 'habitaciones'
rooms_pages = {
    '/': '/habitaciones/',
    '/en/': '/en/rooms/',
    '/de/': '/de/zimmer/',
}

# Función para obtener las URLs relativas y normalizarlas
def get_relative_url(url):
    try:
        path = urlparse(str(url)).path.lower()
        if not path.endswith('/'):
            path += '/'
        return path if path else "INVALID_URL"
    except Exception:
        return "INVALID_URL"

# Función para extraer tokens de una URL
def extract_tokens(url):
    if not url:
        return []
    url = re.sub(r'\.\w+$', '', url)  # Eliminar la extensión (.html, .php, etc.)
    tokens = re.split(r'[\/\-_]', url)
    return [token for token in tokens if token]  # Eliminar tokens vacíos

# Detectar idioma en la URL antigua
def detect_language(url):
    for lang in ['/en/', '/de/', '/fr/']:
        if lang in url:
            return lang
    return '/'  # Por defecto, idioma principal

# Función mejorada para encontrar la URL más parecida con jerarquía y tokens específicos
def match_urls_with_hierarchy_and_tokens(old_url, new_urls):
    try:
        old_tokens = extract_tokens(old_url)
        hierarchy_score = []

        for new_url in new_urls:
            new_tokens = extract_tokens(new_url)
            # Verificar coincidencias exactas de tokens
            shared_tokens = len(set(old_tokens).intersection(new_tokens))
            shared_hierarchy = sum(1 for a, b in zip(old_tokens, new_tokens) if a == b)
            similarity = SequenceMatcher(None, old_url, new_url).ratio()
            hierarchy_score.append((new_url, shared_hierarchy, shared_tokens, similarity))

        # Ordenar por jerarquía > tokens compartidos > similitud
        sorted_urls = sorted(hierarchy_score, key=lambda x: (x[1], x[2], x[3]), reverse=True)

        # Si hay coincidencias significativas, devolver la mejor
        if sorted_urls and (sorted_urls[0][1] > 0 or sorted_urls[0][2] > 0):
            return sorted_urls[0][0]
        else:
            return None  # No hay coincidencia significativa
    except Exception:
        return None

# Lista de páginas de detalles de habitaciones
room_details = [
    '/habitacion-king-vista-mar/',
    '/habitacion-deluxe-vista-mar-lateral/',
    '/habitacion-doble-con-terraza-vista-mar/',
    '/habitacion-estandar-economica/',
    '/habitacion-triple/',
    '/junior-suite/',
    '/habitacion-doble-terraza/',
    '/habitacion-deluxe-vista-mar/',
    '/habitacion-doble-vista-mar-lateral/',
    '/en/junior-suite/',
    '/en/economy-standard-room/',
    '/en/triple-room/',
    '/en/double-room-side-sea-view/',
    '/en/deluxe-room-side-sea-view/',
    '/en/double-room-with-terrace/',
    '/en/deluxe-sea-view-room/',
    '/en/king-sea-view-room/',
    '/en/double-room-with-terrace-sea-view/',
    '/fr/chambre-double-terrasse/',
    '/fr/junior-suite/',
    '/fr/chambre-deluxe-avec-vue-laterale-sur-la-mer/',
    '/fr/chambre-double-avec-terrasse-vue-mer/',
    '/fr/chambre-triple/',
    '/fr/chambre-deluxe-avec-vue-sur-la-mer/',
    '/fr/chambre-double-vue-mer-laterale/',
    '/fr/chambre-standard-economique/',
    '/fr/chambre-king-avec-vue-sur-la-mer/',
    '/de/doppelzimmer-mit-seitlichem-meerblick/',
    '/de/doppelzimmer-mit-terrasse-mit-meerblick/',
    '/de/deluxe-zimmer-mit-meerblick/',
    '/de/doppelzimmer-terrasse/',
    '/de/zimmer-mit-kingsize-bett-und-meerblick/',
    '/de/deluxe-zimmer-mit-seitlichem-meerblick/',
    '/de/junior-suite/',
    '/de/economy-standardzimmer/',
    '/de/dreibettzimmer/',
]

# Procesar las redirecciones con un fallback inteligente
def process_redirection(old_url):
    # Asegurar que old_url termine con '/'
    if not old_url.endswith('/'):
        old_url += '/'

    # Detectar el idioma de la URL antigua
    language = detect_language(old_url)
    original_language = language  # Guardamos el idioma original

    # Verificar si la URL antigua es una página de detalles de habitación
    if old_url in room_details:
        # Si el idioma está disponible en la nueva web
        if language in available_languages:
            return rooms_pages.get(language, '/habitaciones/')
        else:
            # Redirigir a la página de 'habitaciones' en el idioma principal
            return rooms_pages['/']

    # Intentar encontrar la mejor coincidencia en el idioma disponible
    if language in available_languages:
        best_match = match_urls_with_hierarchy_and_tokens(old_url, df["New URLs"].tolist())
        if best_match:
            return best_match
        else:
            # Si no se encuentra coincidencia, redirigir al home del idioma
            return language
    else:
        # Si el idioma no está disponible, reemplazar el idioma por el idioma principal en la URL
        relative_url = old_url.replace(language, '/')
        # Intentar encontrar la mejor coincidencia en el idioma principal
        best_match = match_urls_with_hierarchy_and_tokens(relative_url, df["New URLs"].tolist())
        if best_match:
            return best_match
        else:
            # Si no se encuentra coincidencia, redirigir a la página correspondiente en el idioma principal
            return relative_url

# Interfaz de la aplicación
st.title("Herramienta de Redirecciones Automáticas")
st.write("Sube un archivo Excel con columnas 'Old URLs' y 'New URLs'. La herramienta generará un archivo con las redirecciones.")

# Subir archivo Excel
uploaded_file = st.file_uploader("Sube tu archivo Excel", type="xlsx")

if uploaded_file is not None:
    try:
        # Leer el archivo como Excel
        df = pd.read_excel(uploaded_file)

        # Reemplazar valores NaN por cadenas vacías
        df = df.fillna('')

        # Asegurarse de que todas las celdas sean texto
        df = df.astype(str)

        # Normalizar las URLs
        df["Old URLs"] = df["Old URLs"].apply(get_relative_url)
        df["New URLs"] = df["New URLs"].apply(get_relative_url)

        # Procesar las redirecciones
        df["Redirección"] = df["Old URLs"].apply(process_redirection)

        # Mostrar el resultado
        st.dataframe(df)

        # Permitir descarga del archivo procesado
        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        df.to_excel(writer, index=False, sheet_name='Redirecciones')
        writer.close()
        processed_data = output.getvalue()
        st.download_button(
            label="Descargar Archivo con Redirecciones",
            data=processed_data,
            file_name="Redirecciones_Relativas.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    except Exception as e:
        st.error(f"Ocurrió un error al procesar el archivo: {str(e)}")
