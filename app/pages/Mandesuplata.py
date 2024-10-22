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
1. Las unidades faltantes y el tiempo restante disponible.
2. Si la opción de combinar ramos está activada:
    - Elimina los contenidos menos importantes.
    - Combina en una misma semana los contenidos de distintas unidades que tengan sinergia entre sí.
3. Si la opción de combinar ramos está desactivada:
    - Elimina únicamente los contenidos menos importantes.
    - No se deben mezclar contenidos de distintas unidades en una misma semana.
4. Toda la materia faltante debe ajustarse al tiempo restante disponible, distribuyéndola de manera equitativa semana por semana.
"""

user_template_message = """
Este es el programa del curso:

{programa}

Las unidades o subunidades faltantes son: {unidades_faltantes}. 
El tiempo restante disponible es de {semanas_disponibles} semanas.
{combinacion_texto}

Por favor, genera un nuevo cronograma ajustado semana por semana, comenzando desde la semana 1 de las semanas restantes. 
Indica los contenidos específicos a cubrir en cada semana y justifica tu propuesta.
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
st.write("Sube el programa del curso en PDF, selecciona las unidades faltantes, y genera un cronograma ajustado.")

# Carga del archivo PDF
archivo_pdf = st.file_uploader("Sube el programa del curso (PDF)", type="pdf")

# Input: Unidades faltantes
unidades_faltantes = st.text_area(
    "Ingresa las unidades o subunidades faltantes (por ejemplo: 3.3, 2.1):", 
    placeholder="Escribe las unidades faltantes separadas por comas"
)

# Input: Tiempo disponible
semanas_disponibles = st.number_input(
    "¿Cuántas semanas tienes disponibles?", min_value=1, max_value=16, step=1, value=3
)

# Checkbox para combinar ramos
combinar_ramos = st.checkbox("¿Permitir combinar ramos relacionados?", value=True)

# Generar cronograma si se ha cargado un archivo PDF
if archivo_pdf and st.button("Generar Cronograma Ajustado"):
    with st.spinner("Generando cronograma..."):
        programa_texto = extract_pdf_text(archivo_pdf)

        # Definir el texto adicional según la opción de combinación
        combinacion_texto = (
            "La opción de combinar ramos está activada. Elimina los contenidos menos importantes y combina temas con sinergia en una misma semana."
            if combinar_ramos else
            "La opción de combinar ramos está desactivada. Solo se eliminarán los contenidos menos importantes, sin mezclar unidades en una misma semana."
        )

        # Preparar el input para el template del prompt
        template_prompt_input = {
            "programa": programa_texto,
            "unidades_faltantes": unidades_faltantes,
            "semanas_disponibles": semanas_disponibles,
            "combinacion_texto": combinacion_texto,
        }

        # Invocar el modelo para generar el cronograma
        respuesta_generada = chain.invoke(template_prompt_input)
        st.success("Cronograma generado exitosamente:")
        st.text_area("Cronograma Ajustado Semana por Semana", respuesta_generada, height=400)

# Información adicional
st.info("Esta aplicación utiliza LangChain y la API de OpenAI para reorganizar el cronograma del curso en base a las opciones seleccionadas.")
