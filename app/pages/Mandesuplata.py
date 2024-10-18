import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import dotenv
import os
import PyPDF2

# Configuración de la página de Streamlit
st.set_page_config(
    page_title="Reestructuración de Cronograma de Cursos",
    page_icon="📅",
)

# Cargar las variables de entorno
dotenv.load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# Configuración del modelo LLM con OpenAI
llm = ChatOpenAI(openai_api_key=api_key, model="gpt-3.5-turbo")

# Función para extraer texto del archivo PDF
def extract_pdf_text(file):
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    for page_num in range(len(pdf_reader.pages)):
        text += pdf_reader.pages[page_num].extract_text()
    return text

# Templates para el prompt del modelo
system_template_message = """
Eres un experto en educación. Tu tarea es reorganizar un cronograma de curso dado, considerando:
1. Las semanas de interrupción indicadas.
2. La posibilidad de combinar contenidos si se permite.
3. Optimizar la entrega de los contenidos más importantes en el tiempo restante.
"""

user_template_message = """
Este es el programa del curso:

{programa}

Se han perdido las semanas {semanas_perdidas} debido a un paro.
{combinacion_texto}

Por favor, genera un nuevo cronograma para las semanas restantes, indicando qué contenidos se deben cubrir en cada semana y justificando tu propuesta al final.
"""

prompt_template = ChatPromptTemplate.from_messages(
    messages=[
        ("system", system_template_message),
        ("user", user_template_message),
    ]
)

# Configurar la cadena LLM con LangChain
chain = prompt_template | llm | StrOutputParser()

# Interfaz de usuario con Streamlit
st.markdown("# Reestructuración de Cronograma 📅")
st.write("Sube el programa del curso en PDF, selecciona las opciones, y genera un cronograma ajustado.")

# Carga del archivo PDF
archivo_pdf = st.file_uploader("Sube el programa del curso (PDF)", type="pdf")

# Selección de semanas perdidas
semanas_perdidas = st.multiselect(
    "Selecciona las semanas en las que hubo paro",
    options=list(range(1, 16)),
    default=[11, 12]
)

# Checkbox para combinar unidades
combinar_cursos = st.checkbox("¿Permitir combinar cursos relacionados?", value=True)

# Generar cronograma si se ha cargado un archivo PDF
if archivo_pdf and st.button("Generar Cronograma Ajustado"):
    with st.spinner("Generando cronograma..."):
        programa_texto = extract_pdf_text(archivo_pdf)
        
        # Texto adicional según la opción de combinación
        combinacion_texto = (
            "Se permite combinar cursos relacionados." if combinar_cursos 
            else "No se permite combinar cursos relacionados."
        )

        # Input para el template del prompt
        template_prompt_input = {
            "programa": programa_texto,
            "semanas_perdidas": ', '.join(map(str, semanas_perdidas)),
            "combinacion_texto": combinacion_texto,
        }

        # Invocar el modelo para generar el cronograma
        respuesta_generada = chain.invoke(template_prompt_input)
        st.success("Cronograma generado exitosamente:")
        st.text_area("Cronograma Ajustado", respuesta_generada, height=400)

# Información adicional
st.info("Esta aplicación utiliza LangChain y la API de OpenAI para reorganizar el cronograma del curso en base a las opciones seleccionadas.")
