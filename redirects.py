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
    try:
        # Leer el archivo como Excel
        df = pd.read_excel(uploaded_file)
        
        # Verificar si las columnas necesarias están presentes
        if "Old URLs" not in df.columns or "New URLs" not in df.columns:
            st.error("El archivo debe contener columnas llamadas 'Old URLs' y 'New URLs'.")
        else:
            # Filtrar filas donde ambas columnas tengan datos
            df = df.dropna(subset=["Old URLs", "New URLs"])
            
            # Procesar las redirecciones
            st.write("Procesando las redirecciones...")
            df["Redirección"] = df.apply(
                lambda row: match_urls(row["Old URLs"], df["New URLs"].tolist()), axis=1
            )
            
            # Mostrar el resultado
            st.dataframe(df)
            
            # Permitir descarga del archivo procesado
            output = df.to_excel(index=False)
            st.download_button(
                label="Descargar Archivo con Redirecciones",
                data=output,
                file_name="Redirecciones.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
    except Exception as e:
        st.error(f"Ocurrió un error al procesar el archivo: {str(e)}") 

