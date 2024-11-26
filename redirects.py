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

# Función para encontrar la URL más parecida o redirigir a la home
def match_urls(old_url, new_urls):
    try:
        # Filtrar valores nulos y convertir a cadenas
        cleaned_urls = [str(url) for url in new_urls if pd.notnull(url)]
        
        # Busca la URL más similar utilizando difflib
        match = get_close_matches(old_url, cleaned_urls, n=1, cutoff=0.4)  # Ajustamos el cutoff para ser más permisivo
        return match[0] if match else "/"
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
            # Filtrar filas donde "New URLs" tenga datos
            df = df.dropna(subset=["New URLs"])
            
            # Convertir las URLs a relativas
            df["Old URLs"] = df["Old URLs"].apply(get_relative_url)
            df["New URLs"] = df["New URLs"].apply(get_relative_url)
            
            # Procesar las redirecciones utilizando difflib
            st.write("Procesando las redirecciones...")
            df["Red
