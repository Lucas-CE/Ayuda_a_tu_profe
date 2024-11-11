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
        
        # Mostrar la bibliografía con el título en negritas y botón para buscar en Google
        libros = bibliografia.split("\n")
        for libro in libros:
            if libro.strip():  # Evitar mostrar líneas vacías
                # Extraer el título del texto entre comillas
                inicio = libro.find('"')
                fin = libro.find('"', inicio + 1)
                if inicio != -1 and fin != -1:
                    titulo = libro[inicio+1:fin]
                    autores_y_detalles = libro[:inicio].strip() + libro[fin+1:].strip()
                    
                    # Mostrar el título en negrita y el botón "Buscar en Google"
                    st.markdown(f"**{titulo}** - {autores_y_detalles}")
                    st.markdown(
                        f"[Buscar en Google](https://www.google.com/search?q={titulo.replace(' ', '+')})",
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(f"- {libro.strip()}")
    else:
        st.write("Por favor, ingresa un tema.")

