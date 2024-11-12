import streamlit as st
from langchain_openai import ChatOpenAI
import dotenv
import os

# Configurar OpenAI
dotenv.load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Crear función para generar bibliografía sin links
def buscar_bibliografia_sin_links(tema):
    # Prompt para generar la bibliografía sin enlaces
    prompt = f"Recomienda bibliografía académica sobre el tema '{tema}', sin incluir enlaces o links a sitios web."

    # Inicializar el modelo de ChatGPT
    llm = ChatOpenAI(api_key=OPENAI_API_KEY, temperature=0.7, model="gpt-4o-mini")

    # Procesar el prompt
    response = llm(prompt)
    
    # Devolver solo el contenido del mensaje
    return response.content

# Interfaz en Streamlit
st.title("Buscador de Bibliografía Académica")
tema = st.text_input("Ingresa el tema que deseas estudiar (ej: probabilidades avanzadas):")

if st.button("Buscar"):
    if tema:
        bibliografia = buscar_bibliografia_sin_links(tema)
        st.write("### Bibliografía recomendada:")
        
        # Mostrar la bibliografía sin links
        libros = bibliografia.split("\n")
        for libro in libros:
            if libro.strip():  # Evitar mostrar líneas vacías
                st.markdown(f"- {libro.strip()}")  # Mostrar sin links
    else:
        st.write("Por favor, ingresa un tema.")
