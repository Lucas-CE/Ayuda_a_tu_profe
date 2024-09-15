import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Configurar OpenAI
import dotenv
import os
dotenv.load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Crear función para generar bibliografía
def buscar_bibliografia(tema):
    # Prompt para generar la bibliografía
    prompt = f"Recomienda bibliografía académica sobre el tema '{tema}'."
    
    # Inicializar el modelo de ChatGPT
    llm = ChatOpenAI(api_key=OPENAI_API_KEY, temperature=0.7)

    # Procesar el prompt
    response = llm(prompt)
    
    # Devolver solo el contenido del mensaje
    return response.content

# Interfaz en Streamlit
st.title("Buscador de Bibliografía Académica")
tema = st.text_input("Ingresa el tema que deseas estudiar (ej: probabilidades avanzadas):")

if st.button("Buscar"):
    if tema:
        bibliografia = buscar_bibliografia(tema)

        st.write("### Bibliografía recomendada:")
        
        # Dividir la bibliografía en líneas y enumerarlas manualmente con st.markdown
        libros = bibliografia.split("\n")
        for i, libro in enumerate(libros, start=1):
            if libro.strip():  # Evitar mostrar líneas vacías
                st.markdown(f"{i}. {libro.strip()}")
    else:
        st.write("Por favor, ingresa un tema.")