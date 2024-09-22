import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import dotenv
import os

# Configurar OpenAI
dotenv.load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Crear función para sugerir contenido nuevo basado en la bibliografía o cambiar el syllabus
def planificar_contenidos(programa, bibliografia):
    prompt = f"""Ayuda a planificar el contenido de un curso basado en este programa: {programa}.
                 También incorpora o ajusta las siguientes referencias bibliográficas: {bibliografia}.
                 Sugiéreme cómo cambiar la orientación del curso o diseñar nuevas clases en base a este contenido."""
    
    # Inicializar el modelo de ChatGPT
    llm = ChatOpenAI(api_key=OPENAI_API_KEY, temperature=0.7)
    response = llm(prompt)
    
    # Devolver el contenido generado
    return response.content

# Interfaz en Streamlit
st.title("Planificador de Contenidos para Profesores")

# Input del programa actual del curso
programa = st.text_area("Ingresa el programa actual del curso:", placeholder="Describe el programa o syllabus actual del curso aquí...")

# Input para nueva bibliografía
bibliografia = st.text_area("¿Tienes una nueva bibliografía que quieras incluir?", placeholder="Ingresa aquí las nuevas referencias bibliográficas que quieres usar...")

if st.button("Planificar Nuevas Clases"):
    if programa:
        # Planificar contenidos en base al programa y la nueva bibliografía
        planificacion = planificar_contenidos(programa, bibliografia)
        
        st.write("### Planificación sugerida:")
        st.write(planificacion)
    else:
        st.write("Por favor, ingresa el programa actual del curso para continuar.")