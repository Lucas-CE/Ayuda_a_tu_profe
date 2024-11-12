import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import dotenv
import os
from utils.pdf_utils import extract_text_from_pdf

# Configuración de la página de Streamlit
st.set_page_config(
    page_title="Reestructuración de Cronograma de Cursos",
    page_icon="📅",
)

# Cargar las variables de entorno
dotenv.load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# Configuración del modelo LLM con OpenAI
llm = ChatOpenAI(openai_api_key=api_key, model="gpt-4o-mini")

# Templates para el prompt del modelo
system_template_message = """
Eres un experto en educación. Tu tarea es reorganizar un cronograma de curso dado, considerando:
1. Las unidades faltantes y el tiempo restante disponible.
2. Si la opción de combinar unidades está activada:
    - Elimina los contenidos menos importantes.
    - Combina en una misma semana los contenidos de distintas unidades que tengan sinergia entre sí.
3. Si la opción de combinar unidades está desactivada:
    - Elimina únicamente los contenidos menos importantes.
    - No se deben mezclar contenidos de distintas unidades en una misma semana.
4. Toda la materia faltante debe ajustarse al tiempo restante disponible, distribuyéndola de manera equitativa semana por semana.
5. Asegúrate de que cada contenido incluya el identificador de unidad correspondiente (por ejemplo: Unidad 4.1).
6. Al final de tu respuesta, lista las subunidades que no fueron incluidas en el cronograma debido a falta de tiempo o relevancia.
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
st.write("Esta herramienta permite reorganizar un cronograma de curso basado en las semanas disponibles restantes. Analiza dinámicamente las unidades y subunidades faltantes a partir de la última unidad alcanzada y genera un plan ajustado priorizando los temas más importantes.")
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

# Checkbox para combinar unidades
combinar_unidades = st.checkbox("¿Permitir combinar unidades relacionadas?", value=True)

# Generar cronograma si se ha cargado un archivo PDF
if archivo_pdf and st.button("Generar Cronograma Ajustado", key="generar_cronograma"):
    with st.spinner("Generando cronograma..."):
        programa_texto = extract_text_from_pdf(archivo_pdf)

        # Definir el texto adicional según la opción de combinación
        combinacion_texto = (
            "La opción de combinar unidades está activada. Elimina los contenidos menos importantes y combina temas con sinergia en una misma semana."
            if combinar_unidades else
            "La opción de combinar unidades está desactivada. Solo se eliminarán los contenidos menos importantes, sin mezclar unidades en una misma semana."
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

        # Identificar subunidades no incluidas
        unidades_faltantes_lista = [unidad.strip() for unidad in unidades_faltantes.split(",")]
        incluidas = [unidad for unidad in unidades_faltantes_lista if unidad in respuesta_generada]
        no_incluidas = [unidad for unidad in unidades_faltantes_lista if unidad not in respuesta_generada]

        # Mostrar resultados
        # Mostrar resultados
        st.success("Cronograma generado exitosamente:")
        st.markdown("### Cronograma Ajustado Semana por Semana")
        st.write(respuesta_generada)
    

        if no_incluidas:
            st.warning(f"Subunidades no incluidas: {', '.join(no_incluidas)}")

# Información adicional
st.info("Esta aplicación utiliza LangChain y la API de OpenAI para reorganizar el cronograma del curso en base a las opciones seleccionadas.")
