import streamlit as st
import pandas as pd
from urllib.parse import urlparse
from difflib import SequenceMatcher
from io import BytesIO
import re

# Lista centralizada de idiomas admitidos
SUPPORTED_LANGUAGES = ['/en/', '/de/', '/fr/', '/it/', '/pt/']  # Agrega más idiomas aquí
DEFAULT_LANGUAGE = '/en/'  # Idioma principal al que redirigir si el idioma no existe

# Función para obtener las URLs relativas y normalizarlas
def get_relative_url(url):
    try:
        path = urlparse(str(url)).path.lower().rstrip('/')
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
def detect_language(url, available_languages):
    for lang in SUPPORTED_LANGUAGES:
        if lang in url and lang in available_languages:
            return lang
    # Si el idioma no está disponible, redirigir al idioma principal
    return DEFAULT_LANGUAGE

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
            return None  # No significant match
    except Exception:
        return None

# Procesar las redirecciones con un fallback inteligente
def process_redirection(old_url):
    # Obtener los idiomas disponibles en las URLs nuevas
    available_languages = {lang for lang in SUPPORTED_LANGUAGES if any(lang in url for url in df["New URLs"])}
    # Intentar encontrar la mejor coincidencia
    best_match = match_urls_with_hierarchy_and_tokens(old_url, df["New URLs"].tolist())
    if best_match:
        return best_match
    else:
        # Si no hay coincidencia, asignar según el idioma detectado
        return detect_language(old_url, available_languages)

# Interfaz de la aplicación
st.title("Herramienta de Redirecciones Automáticas")
st.write("Sube un archivo Excel con columnas 'Old URLs' y 'New URLs'. La herramienta generará un archivo con las redirecciones.")

# Subir archivo Excel
uploaded_file = st.file_uploader("Sube tu archivo Excel", type="xlsx")

if uploaded_file is not None:
    try:
        # Leer el archivo como Excel
        df = pd.read_excel(uploaded_file)

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
