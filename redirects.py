import streamlit as st
import pandas as pd
from urllib.parse import urlparse
from difflib import SequenceMatcher
from io import BytesIO
import re

# Función para validar el formato de una URL
def validate_url_format(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

# Función para obtener las URLs relativas y normalizarlas
def get_relative_url(url):
    try:
        path = urlparse(str(url)).path.lower().rstrip('/')
        return path
    except Exception:
        return None

# Función para extraer tokens de una URL
def extract_tokens(url):
    if not url:
        return []
    url = re.sub(r'\.\w+$', '', url)  # Eliminar la extensión (.html, .php, etc.)
    tokens = re.split(r'[\/\-_]', url)
    return [token for token in tokens if token]  # Eliminar tokens vacíos

# Función para encontrar la URL más parecida con jerarquía
def match_urls_with_hierarchy(old_url, new_urls):
    try:
        old_tokens = extract_tokens(old_url)
        hierarchy_score = []

        for new_url in new_urls:
            new_tokens = extract_tokens(new_url)
            shared_hierarchy = sum(1 for a, b in zip(old_tokens, new_tokens) if a == b)
            shared_tokens = len(set(old_tokens).intersection(new_tokens))
            similarity = SequenceMatcher(None, old_url, new_url).ratio()
            hierarchy_score.append((new_url, shared_hierarchy, shared_tokens, similarity))

        # Ordenar por jerarquía > tokens compartidos > similitud
        sorted_urls = sorted(hierarchy_score, key=lambda x: (x[1], x[2], x[3]), reverse=True)
        if sorted_urls and sorted_urls[0][3] > 0.5:  # Similitud mínima requerida
            return sorted_urls[0][0]
        else:
            return "NO_REDIRECTION"
    except Exception:
        return "NO_REDIRECTION"

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

        # Verificar si las columnas necesarias están presentes
        if "Old URLs" not in df.columns or "New URLs" not in df.columns:
            st.error("El archivo debe contener columnas llamadas 'Old URLs' y 'New URLs'.")
        else:
            # Validar formato de las URLs
            df["Valid Old URL"] = df["Old URLs"].apply(validate_url_format)
            df["Valid New URL"] = df["New URLs"].apply(validate_url_format)

            # Filtrar URLs no válidas
            invalid_urls = df[~df["Valid Old URL"] | ~df["Valid New URL"]]
            if not invalid_urls.empty:
                st.warning("Algunas URLs no tienen un formato válido y serán omitidas.")
                st.dataframe(invalid_urls)

            df = df[df["Valid Old URL"] & df["Valid New URL"]]

            # Convertir las URLs a relativas y normalizarlas
            df["Old URLs"] = df["Old URLs"].apply(get_relative_url)
            df["New URLs"] = df["New URLs"].apply(get_relative_url)

            # Procesar las redirecciones utilizando la función mejorada
            st.write("Procesando las redirecciones...")
            df["Redirección"] = df["Old URLs"].apply(
                lambda old_url: match_urls_with_hierarchy(old_url, df["New URLs"].tolist())
            )

            # Estadísticas
            total_urls = len(df)
            no_redirection_count = len(df[df["Redirección"] == "NO_REDIRECTION"])
            st.write(f"Total de URLs procesadas: {total_urls}")
            st.write(f"Redirecciones exitosas: {total_urls - no_redirection_count}")
            st.write(f"URLs sin redirección asignada: {no_redirection_count}")

            # Mostrar URLs sin redirección asignada
            if no_redirection_count > 0:
                st.warning("Algunas URLs no tienen redirección asignada. Revísalas a continuación.")
                st.dataframe(df[df["Redirección"] == "NO_REDIRECTION"])

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
