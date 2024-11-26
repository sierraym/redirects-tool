import streamlit as st
import pandas as pd
from urllib.parse import urlparse
from difflib import SequenceMatcher
from io import BytesIO
import re

# Función para obtener las URLs relativas y normalizarlas
def get_relative_url(url):
    try:
        path = urlparse(url).path.lower().rstrip('/')
        return path
    except Exception:
        return None

# Función para extraer tokens de una URL
def extract_tokens(url):
    if not url:
        return []
    # Eliminar la extensión y dividir por '/', '-', '_'
    url = re.sub(r'\.\w+$', '', url)  # Eliminar la extensión (.html, .php, etc.)
    tokens = re.split(r'[\/\-_]', url)
    tokens = [token for token in tokens if token]  # Eliminar tokens vacíos
    return tokens

# Función mejorada para encontrar la URL más parecida
def match_urls_improved(old_url, new_urls):
    try:
        cleaned_new_urls = [str(url).lower().rstrip('/') for url in new_urls if pd.notnull(url)]
        if not cleaned_new_urls:
            return "/"

        # Extraer tokens de la old_url
        old_tokens = set(extract_tokens(old_url))

        # Crear una lista con la cantidad de tokens compartidos
        matches = []
        for new_url in cleaned_new_urls:
            new_tokens = set(extract_tokens(new_url))
            shared_tokens = old_tokens.intersection(new_tokens)
            matches.append((new_url, len(shared_tokens)))

        # Filtrar las URLs que comparten al menos un token
        token_matches = [match for match in matches if match[1] > 0]

        if token_matches:
            # Ordenar por la cantidad de tokens compartidos y luego por similitud
            token_matches_sorted = sorted(token_matches, key=lambda x: x[1], reverse=True)
            top_matches = [match[0] for match in token_matches_sorted if match[1] == token_matches_sorted[0][1]]
            
            # Si hay múltiples top matches, usar SequenceMatcher para elegir el mejor
            if len(top_matches) > 1:
                similarities = [(url, SequenceMatcher(None, old_url, url).ratio()) for url in top_matches]
                best_match = max(similarities, key=lambda x: x[1])
                return best_match[0]
            else:
                return token_matches_sorted[0][0]
        else:
            # Si no hay coincidencias de tokens, usar similitud general
            similarities = [(new_url, SequenceMatcher(None, old_url, new_url).ratio()) for new_url in cleaned_new_urls]
            best_match = max(similarities, key=lambda x: x[1])
            return best_match[0]
    except Exception:
        return "/"

# Interfaz de la aplicación
st.title("Herramienta de Redirecciones Automáticas Mejorada")
st.write("Sube un archivo Excel con columnas 'Old URLs' y 'New URLs'. La herramienta generará un archivo con las redirecciones.")

# Subir archivo Excel
uploaded_file = st.file_uploader("Sube tu archivo Excel", type="xlsx")

if uploaded_file is not None:
    try:
        # Leer el archivo como Excel
        df = pd.read_excel(uploaded_file)

        # Verificar si las columnas necesarias están presentes
        if "Old URLs" not in df.columns or "New URLs" not in df.columns:
            st.error("El archivo debe contener columnas llamadas 'Old URLs' y 'New URLs'.")
        else:
            # Filtrar filas donde 'Old URLs' tenga datos
            df = df.dropna(subset=["Old URLs"])

            # Convertir las URLs a relativas y normalizarlas
            df["Old URLs"] = df["Old URLs"].apply(get_relative_url)
            df["New URLs"] = df["New URLs"].apply(get_relative_url)

            # Procesar las redirecciones utilizando la función mejorada
            st.write("Procesando las redirecciones...")
            df["Redirección"] = df["Old URLs"].apply(
                lambda old_url: match_urls_improved(old_url, df["New URLs"].tolist())
            )

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
