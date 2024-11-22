import streamlit as st
import openai
import pandas as pd

# Configuración de la API de OpenAI
openai.api_key = "TU_API_KEY"  # Reemplaza con tu clave de API de OpenAI

def match_urls(old_url, new_urls):
    prompt = f"Encuentra la mejor coincidencia para esta URL: {old_url}, entre estas opciones: {', '.join(new_urls)}"
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=100,
    )
    return response.choices[0].text.strip()

# Interfaz de la aplicación
st.title("Herramienta de Redirecciones Automáticas")
st.write("Sube un archivo Excel con columnas 'Old URLs' y 'New URLs'. La herramienta generará un archivo con las redirecciones.")

# Subir archivo Excel
uploaded_file = st.file_uploader("Sube tu archivo Excel", type="xlsx")

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    
    # Verificar que las columnas requeridas existen
    if "Old URLs" in df.columns and "New URLs" in df.columns:
        st.write("Procesando las redirecciones...")
        
        # Generar redirecciones
        df["Redirección"] = df.apply(
            lambda row: match_urls(row["Old URLs"], df["New URLs"].tolist()), axis=1
        )
        
        st.write("Archivo procesado. Descárgalo a continuación.")
        st.dataframe(df)  # Muestra el resultado en la web

        # Permitir descarga del archivo
        st.download_button(
            "Descargar Archivo con Redirecciones",
            data=df.to_excel(index=False),
            file_name="Redirecciones.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    else:
        st.error("El archivo debe contener las columnas 'Old URLs' y 'New URLs'.")
