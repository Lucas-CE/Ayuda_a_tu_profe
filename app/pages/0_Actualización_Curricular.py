import streamlit as st
import markdown
import io
from xhtml2pdf import pisa
from langchain_openai import ChatOpenAI
import PyPDF2

# Configuración de la página
st.set_page_config(
    page_title="Actualización del Programa",
    page_icon="📚",
)

# Cargar variables de entorno
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

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

# Función para convertir Markdown a HTML
def convert_markdown_to_html(markdown_text):
    return markdown.markdown(markdown_text)

# Función para convertir HTML a PDF y retornar un archivo en memoria
def convert_html_to_pdf_memory(source_html):
    pdf_output = io.BytesIO()
    pisa_status = pisa.CreatePDF(io.StringIO(source_html), dest=pdf_output)
    pdf_output.seek(0)
    return pdf_output if not pisa_status.err else None

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

        # Convertir la respuesta a HTML
        html_content = convert_markdown_to_html(response.content)

        # Mostrar el resultado generado
        st.markdown("### Planificación sugerida:")
        st.write(response.content)

        # Generar el PDF desde HTML en memoria
        pdf_output = convert_html_to_pdf_memory(html_content)
        
        if pdf_output:
            # Botón para descargar el PDF
            st.download_button(label="Descargar Planificación en PDF", data=pdf_output, file_name="planificacion_actualizacion_curso.pdf", mime="application/pdf")
        else:
            st.error("Error al generar el PDF.")
        
    else:
        st.error("Por favor, sube el programa del curso.")
