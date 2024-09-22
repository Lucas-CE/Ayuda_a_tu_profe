import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import SimpleJsonOutputParser
import dotenv
import os
import PyPDF2
from fpdf import FPDF

# Configuración de la página
st.set_page_config(
    page_title="Planificación y Actualización Curricular",
    page_icon="📚",
)

# Cargar variables de entorno
dotenv.load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(openai_api_key=api_key, model="gpt-4")

# Plantilla para el sistema
system_template_message = """
Eres un profesor experto en planificar y actualizar programas de estudios en la disciplina {subject}.
"""

user_template_message = """
Basado en el siguiente programa de estudios:
{course_program}

y en los siguientes comentarios del profesor:
{teacher_comments}

Sugiéreme cómo reorganizar y actualizar los contenidos del curso, añadiendo nuevos temas o ajustando el enfoque para alinearlo con los avances recientes en la disciplina.
"""

output_plan_template = """
El output debe ser un objeto JSON con las siguientes llaves:
- tema_1: el tema sugerido
- descripción_1: descripción del tema y enfoque propuesto
- recomendación_1: recomendación de reorganización o ajuste del contenido

Ejemplo:
{{
    "tema_1": "Introducción a la inteligencia artificial",
    "descripción_1": "Se propone un enfoque inicial sobre los principios básicos de IA.",
    "recomendación_1": "Colocar este tema al inicio del curso para sentar las bases."
}}
"""

# Función para leer archivos PDF
def read_pdf(file):
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    for page_num in range(len(pdf_reader.pages)):
        text += pdf_reader.pages[page_num].extract_text()
    return text

# Función para generar críticas y recomendaciones
def analyze_and_critique_program(program, new_topic, teacher_comments):
    """
    Analiza críticamente el programa actual y sugiere mejoras.
    """
    # 1. Revisar objetivos y resultados de aprendizaje actuales
    objectives = program.get('objectives', '')
    learning_outcomes = program.get('learning_outcomes', '')

    # 2. Revisar si el nuevo tema se alinea con los objetivos actuales
    critiques = []
    if new_topic not in objectives:
        critiques.append(f"El nuevo tema '{new_topic}' no parece estar alineado con los objetivos actuales del curso.")
    else:
        critiques.append(f"El nuevo tema '{new_topic}' se ajusta bien a los objetivos del curso.")

    # 3. Revisar si el programa cubre suficientemente otros aspectos
    if 'machine learning' not in learning_outcomes.lower():
        critiques.append("Se recomienda actualizar los resultados de aprendizaje para incluir habilidades prácticas en Machine Learning.")
    
    if 'herramientas de software' not in program.get('indicators', '').lower():
        critiques.append("Se sugiere agregar indicadores que midan el uso efectivo de herramientas tecnológicas como Python o R para análisis de datos.")

    # 4. Sugerencias adicionales de temas
    critiques.append("Considerar la inclusión de temas como Big Data o inteligencia artificial en la gestión de demanda.")
    
    # 5. Recomendaciones adicionales basadas en los comentarios del profesor
    if 'extensión de unidad' in teacher_comments.lower():
        critiques.append("Revisar si la extensión propuesta de la unidad afectará el tiempo dedicado a otros contenidos.")
    
    return critiques

# Función para crear el PDF con las recomendaciones
def create_pdf(critique_list, file_name="recomendaciones_programa.pdf"):
    """
    Genera un PDF con las críticas y recomendaciones proporcionadas.
    """
    pdf = FPDF()
    pdf.add_page()
    
    # Título del documento
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Recomendaciones y Críticas del Programa", ln=True, align="C")
    
    # Añadir el contenido de las críticas
    pdf.set_font("Arial", size=12)
    for critique in critique_list:
        pdf.ln(10)
        pdf.multi_cell(0, 10, txt=critique)
    
    # Guardar el PDF
    pdf.output(file_name)

# Interfaz de Streamlit
st.markdown("# Herramienta de Planificación y Actualización Curricular")

# Input de los parámetros
subject = st.text_input("Ingresa el nombre del curso")
uploaded_program = st.file_uploader("Sube el programa del curso (PDF)", type=["pdf"])

# Espacio para que el profesor ingrese sus ideas sobre los cambios
idea_profesor = st.text_area("Ingresa tus ideas o comentarios sobre los cambios que deseas realizar en el curso:")

# Leer archivo PDF
program_text = ""

if uploaded_program:
    program_text = read_pdf(uploaded_program)
    st.success("Programa cargado correctamente.")

# Generar la planificación
if st.button("Generar Planificación"):
    if program_text:
        # Crear el prompt para el modelo
        complete_user_template_message = user_template_message + output_plan_template
        prompt_template = ChatPromptTemplate.from_messages(
            messages=[
                ("system", system_template_message),
                ("user", complete_user_template_message),
            ]
        )
        chain = prompt_template | llm | SimpleJsonOutputParser()

        # Input para el modelo
        prompt_input = {
            "course_program": program_text,
            "teacher_comments": idea_profesor,
            "subject": subject,
        }

        # Generar la planificación
        plan_json = chain.invoke(prompt_input)
        
        # Mostrar el resultado generado
        st.markdown("### Planificación sugerida:")
        for i in range(len(plan_json) // 3):
            st.write(f"**Tema {i+1}:** {plan_json[f'tema_{i+1}']}")
            st.write(f"**Descripción:** {plan_json[f'descripción_{i+1}']}")
            st.write(f"**Recomendación:** {plan_json[f'recomendación_{i+1}']}")

        # Generar críticas y recomendaciones
        critiques = analyze_and_critique_program(
            program={"objectives": program_text, "learning_outcomes": "", "indicators": ""}, 
            new_topic="Machine Learning en pronósticos de demanda", 
            teacher_comments=idea_profesor
        )

        # Crear el PDF con las recomendaciones
        create_pdf(critiques)

        st.success("PDF con recomendaciones creado exitosamente.")
        with open("recomendaciones_programa.pdf", "rb") as pdf_file:
            st.download_button(label="Descargar PDF", data=pdf_file, file_name="recomendaciones_programa.pdf")

    else:
        st.error("Por favor, sube el programa del curso.")
