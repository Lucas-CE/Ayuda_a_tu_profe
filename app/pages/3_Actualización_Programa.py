import streamlit as st 
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import SimpleJsonOutputParser
import dotenv
import os
import PyPDF2   
from app.pdf_generador import generar_pdf  # Importa la nueva función


# Configuración de la página
st.set_page_config(
        page_title="Planificador de Contenidos",
    page_icon="📚",
)

# Cargar variables de entorno
dotenv.load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Inicializar LLM
llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY, model="gpt-4o-mini")

# Función para leer archivos PDF
def read_pdf(file):
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    for page_num in range(len(pdf_reader.pages)):
        text += pdf_reader.pages[page_num].extract_text()
    return text

# Función para crear un prompt más estructurado
def generar_prompt(programa_curso, comentarios_profesor, materia):
    prompt = f"""
    Eres un profesor experto en planificar y actualizar programas de estudios en {materia}.
    A continuación te doy el programa actual del curso y comentarios del profesor:
    
    Programa del curso:
    {programa_curso}

    Comentarios del profesor:
    {comentarios_profesor}

    Con base en esto, sugiéreme una actualización del curso, incluyendo:
    - Nuevos temas o cambios en el enfoque
    - Estrategias de evaluación adecuadas para los cambios
    - Resultados de aprendizaje esperados
    - Bibliografía adicional (si es necesario)
    
    Además, ten en consideración que la duración del curso no debe superar 15 semanas.
    """
    return prompt

# Función para limpiar la respuesta del modelo
def limpiar_respuesta(respuesta):
    # Acceder al contenido de la respuesta de AIMessage
    contenido = respuesta.content
    # Eliminar metadatos no deseados
    inicio = contenido.find("Actualización del curso:")
    if inicio != -1:
        respuesta_limpia = contenido[inicio:]  # Mantener solo desde la sección relevante
        return respuesta_limpia.replace("\\n", "\n").strip()  # Formatear y limpiar saltos de línea
    return contenido

# Interfaz de Streamlit
st.markdown("# Herramienta de Actualización Curricular")

# Input de los parámetros
materia = st.text_input("Ingresa el nombre del curso")
uploaded_program = st.file_uploader("Sube el programa del curso (PDF)", type=["pdf"])

# Espacio para que el profesor ingrese sus ideas sobre los cambios
comentarios_profesor = st.text_area("Ingresa ideas o comentarios sobre los cambios que deseas realizar en el curso:")

# Leer archivo PDF
program_text = ""

if uploaded_program:
    program_text = read_pdf(uploaded_program)
    st.success("Programa cargado correctamente.")

# Generación del PDF
if st.button("Generar Planificación"):
    if program_text:
        # Crear el prompt para el modelo
        prompt = generar_prompt(program_text, comentarios_profesor, materia)

        # Llamar al modelo con el prompt
        response = llm(prompt)

        # Limpiar la respuesta para quitar los metadatos innecesarios
        respuesta_limpia = limpiar_respuesta(response)

        # Mostrar el resultado generado
        st.markdown("### Planificación sugerida:")
        st.write(respuesta_limpia)
        
        # Generar el PDF
        pdf_file = generar_pdf(respuesta_limpia)

        # Botón para descargar el PDF
        st.download_button(label="Descargar Planificación en PDF", data=pdf_file, file_name=f"planificacion_{materia}.pdf", mime="application/pdf")
   
    else:
        st.error("Por favor, sube el programa del curso.")
