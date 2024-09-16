import streamlit as st
from PyPDF2 import PdfReader # type: ignore
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import dotenv
import os

# Cargar la clave API de OpenAI
dotenv.load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Función para extraer texto del PDF
def extraer_texto_pdf(pdf_file):
    reader = PdfReader(pdf_file)
    texto = ""
    for page in reader.pages:
        texto += page.extract_text()
    return texto

# Función para planificar contenido
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

# Cargar programa en PDF
programa_pdf = st.file_uploader("Sube el programa del curso en formato PDF", type="pdf")
bibliografia_input = st.text_area("Ingresa la nueva bibliografía o deja en blanco si no la deseas modificar:")

programa_texto = ""
if programa_pdf:
    programa_texto = extraer_texto_pdf(programa_pdf)
    st.write("Texto extraído del programa:")
    st.write(programa_texto)

if st.button("Planificar Nuevas Clases"):
    if programa_texto:
        # Planificar contenido basado en el programa extraído y la bibliografía proporcionada
        planificacion = planificar_contenidos(programa_texto, bibliografia_input)
        
        st.write("### Planificación sugerida:")
        st.write(planificacion)
    else:
        st.write("Por favor, sube un PDF con el programa del curso.")