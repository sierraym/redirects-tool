import streamlit as st
import pandas as pd
from urllib.parse import urlparse
from difflib import SequenceMatcher
from io import BytesIO

# Función para obtener las URLs relativas y normalizarlas
def get_relative_url(url):
    try:
        path = urlparse(url).path.lower().rstrip('/')
        return path
    except Exception:
        return None

# Función para encontrar la URL más parecida utilizando SequenceMatcher de difflib
def match_urls(old_url, new_urls):
    try:
        cleaned_urls = [str(url).lower().rstrip('/') for url in new_urls if pd.notnull(url)]
        if not cleaned_urls:
            return "/"

        # Calcular la similitud entre old_url y cada new_url
        similarities = [(new_url, SequenceMatcher(None, old_url, new_url).ratio()) for new_url in cleaned_urls]

        # Encontrar la new_url con la mayor similitud
        best_match = max(similarities, key=lambda x: x[1])

        return best_match[0]
    except Exception:
        return "/"

# Interfaz de la aplicación
st.title("Herramienta de Redirecciones Automáticas")
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

            # Procesar las redirecciones utilizando difflib SequenceMatcher
            st.write("Procesando las redirecciones...")
            df["Redirección"] = df["Old URLs"].apply(
                lambda old_url: match_urls(old_url, df["New URLs"].tolist())
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
