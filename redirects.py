import streamlit as st
import pandas as pd
from urllib.parse import urlparse
from difflib import get_close_matches

# Función para obtener las URLs relativas
def get_relative_url(url):
    try:
        return urlparse(url).path  # Extrae solo la parte relativa de la URL (/ruta/relativa)
    except Exception:
        return None  # Devuelve None si hay algún error

# Función para encontrar la URL más parecida
def match_urls(old_url, new_urls):
    try:
        # Busca la URL más similar utilizando difflib
        match = get_close_matches(old_url, new_urls, n=1, cutoff=0.6)
        return match[0] if match else "Sin coincidencias"
    except Exception:
        return "Error en la coincidencia"

# Interfaz de la aplicación
st.title("Herramienta de Redirecciones Automáticas (Sin OpenAI)")
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
            # Filtrar filas donde ambas columnas tengan datos
            df = df.dropna(subset=["Old URLs", "New URLs"])
            
            # Convertir las URLs a relativas
            df["Old URLs"] = df["Old URLs"].apply(get_relative_url)
            df["New URLs"] = df["New URLs"].apply(get_relative_url)
            
            # Procesar las redirecciones utilizando difflib
            st.write("Procesando las redirecciones...")
            df["Redirección"] = df["Old URLs"].apply(
                lambda old_url: match_urls(old_url, df["New URLs"].tolist())
            )
            
            # Mostrar el resultado
            st.dataframe(df)
            
            # Permitir descarga del archivo procesado
            output = df.to_excel(index=False)
            st.download_button(
                label="Descargar Archivo con Redirecciones",
                data=output,
                file_name="Redirecciones_Relativas.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
    except Exception as e:
        st.error(f"Ocurrió un error al procesar el archivo: {str(e)}")
