import streamlit as st
import pandas as pd
from urllib.parse import urlparse
from difflib import get_close_matches
from io import BytesIO
# Asegúrate de tener instalada la librería Levenshtein
# Puedes instalarla con: pip install python-Levenshtein
import Levenshtein

# Función para normalizar y obtener las URLs relativas
def normalize_url(url):
    try:
        parsed_url = urlparse(url.lower().strip())
        path = parsed_url.path.rstrip('/')
        return path
    except Exception:
        return None

# Función para encontrar la URL más parecida utilizando Levenshtein
def match_urls(old_url, new_urls):
    try:
        cleaned_urls = [str(url) for url in new_urls if pd.notnull(url)]
        # Calcular la distancia Levenshtein para cada URL nueva
        distances = [(url, Levenshtein.distance(old_url, url)) for url in cleaned_urls]
        # Ordenar las URLs por distancia mínima
        distances.sort(key=lambda x: x[1])
        return distances[0][0] if distances else "/"
    except Exception:
        return "/"

# Interfaz de la aplicación
st.title("Herramienta de Redirecciones Automáticas Mejorada")
st.write("Sube un archivo Excel con columnas 'Old URLs' y 'New URLs'. La herramienta generará un archivo con las redirecciones.")

# Parámetros ajustables
st.sidebar.header("Parámetros de Coincidencia")
similarity_method = st.sidebar.selectbox("Método de Similitud", ["Difflib", "Levenshtein"])
if similarity_method == "Difflib":
    cutoff = st.sidebar.slider("Nivel de sensibilidad (cutoff)", 0.0, 1.0, 0.4)
else:
    cutoff = None  # No se utiliza en Levenshtein

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
            
            # Normalizar las URLs
            df["Old URLs"] = df["Old URLs"].apply(normalize_url)
            df["New URLs"] = df["New URLs"].apply(normalize_url)
            
            # Procesar las redirecciones
            st.write("Procesando las redirecciones...")
            if similarity_method == "Difflib":
                df["Redirección"] = df["Old URLs"].apply(
                    lambda old_url: get_close_matches(old_url, df["New URLs"].dropna().tolist(), n=1, cutoff=cutoff)
                )
                df["Redirección"] = df["Redirección"].apply(lambda x: x[0] if x else "/")
            else:
                df["Redirección"] = df["Old URLs"].apply(
                    lambda old_url: match_urls(old_url, df["New URLs"].tolist())
                )
            
            # Mostrar el resultado
            st.dataframe(df)
            
            # Permitir descarga del archivo procesado
            output_format = st.selectbox("Seleccione el formato de descarga", ["Excel", "CSV"])
            if output_format == "Excel":
                # Crear un objeto BytesIO para guardar el archivo Excel en memoria
                output = BytesIO()
                writer = pd.ExcelWriter(output, engine='xlsxwriter')
                df.to_excel(writer, index=False, sheet_name='Redirecciones')
                writer.save()
                processed_data = output.getvalue()
                mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                file_ext = "xlsx"
            else:
                # Convertir el DataFrame a CSV y codificarlo como bytes
                processed_data = df.to_csv(index=False).encode('utf-8')
                mime_type = "text/csv"
                file_ext = "csv"
            st.download_button(
                label="Descargar Archivo con Redirecciones",
                data=processed_data,
                file_name=f"Redirecciones_Relativas.{file_ext}",
                mime=mime_type,
            )
    except Exception as e:
        st.error(f"Ocurrió un error al procesar el archivo: {str(e)}")
