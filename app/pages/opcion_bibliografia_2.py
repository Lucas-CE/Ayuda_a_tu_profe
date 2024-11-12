import streamlit as st
from langchain_openai import ChatOpenAI
import dotenv
import os

# Configurar OpenAI
dotenv.load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Crear función para generar bibliografía con links verificados (en la medida de lo posible)
def buscar_bibliografia_con_links(tema):
    # Prompt para generar la bibliografía con enlaces verificados
    prompt = f"Recomienda bibliografía académica sobre el tema '{tema}', incluyendo solo enlaces que sean accesibles y válidos. No incluyas enlaces falsos o que puedan estar inactivos."

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
        bibliografia = buscar_bibliografia_con_links(tema)
        st.write("### Bibliografía recomendada:")
        
        # Mostrar la bibliografía con links (con riesgo de links no válidos)
        libros = bibliografia.split("\n")
        for libro in libros:
            if libro.strip():  # Evitar mostrar líneas vacías
                st.markdown(f"{libro.strip()}")  # Mostrar links
    else:
        st.write("Por favor, ingresa un tema.")
