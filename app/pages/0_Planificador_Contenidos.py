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
    page_title="Planificador de Contenidos",
    page_icon="📚",
)

# Cargar variables de entorno
dotenv.load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY, model="gpt-4o-mini")

# Plantilla para el sistema
system_template_message = """
Eres un profesor experto en planificar y actualizar programas de estudios en el tema {subject}.
"""

# Plantilla ampliada para el usuario
user_template_message = """
Basado en el siguiente programa de estudios:
{course_program}

y en los siguientes comentarios del profesor:
{teacher_comments}

Sugiéreme cómo reorganizar y actualizar los contenidos del curso, añadiendo nuevos temas, ajustando el enfoque, estrategias de evaluación y resultados de aprendizaje para alinearlos con los avances recientes en el tema.
"""

output_plan_template = """
El output debe ser un objeto JSON con las siguientes llaves:
- Tema: el tema sugerido
- Contenidos: subtemas del tema principal
- Indicador de logro: lo que se espera que el estudiante logre
- Estrategias de evaluación: propuestas de evaluación que miden los logros
- Resultados de aprendizaje: objetivos que los estudiantes deben alcanzar
<<<<<<< HEAD:app/pages/0_Planificador_Contenidos.py
- Bibliografía del tema: en formato APA
=======
- Bibliografía: Una lista de referencias relevantes para el tema en formato APA
>>>>>>> 6d7403b1397233389acda1c5ccc008b71112dd32:app/pages/_Planificador_Contenidos.py

Ejemplo:
{{
    "Tema": "Ética y responsabilidad en el uso de IA",
    "Contenidos": [
        "4.1. Sesgos y discriminación en la IA",
        "4.2. Privacidad y seguridad de los datos",
        "4.3. Responsabilidad social y legal en la IA"
    ],
    "Indicador de logro": [
        "El estudiante comprende dimensiones éticas del uso de IA",
        "El estudiante reconoce riesgos de sesgo en IA"
    ],
    "Estrategias de evaluación": [
        "Participación en discusiones",
        "Estudio de casos sobre sesgo en IA"
    ],
    "Resultados de aprendizaje": [
        "Comprende los riesgos de sesgo en la IA",
        "Evalúa aplicaciones éticas de IA"
    ],
    "Bibliografía del tema": [
        "Guzmán-Valenzuela et al., 2021",
        "Hakimi et al., 2021",
        "O’Neil, 2016"
    ]
}}
"""

# Función para leer archivos PDF
def read_pdf(file):
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    for page_num in range(len(pdf_reader.pages)):
        text += pdf_reader.pages[page_num].extract_text()
    return text

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
idea_profesor = st.text_area("Ingresa ideas o comentarios sobre los cambios que deseas realizar en el curso:")

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
        if isinstance(plan_json, list):
            for i, tema in enumerate(plan_json):
                st.write(f"**Tema {i+1}:** {tema.get('Tema')}")
                st.write(f"**Contenidos:** {tema.get('Contenidos')}")
                st.write(f"**Indicador de logro:** {tema.get('Indicador de logro')}")
                st.write(f"**Estrategias de evaluación:** {tema.get('Estrategias de evaluación')}")
                st.write(f"**Resultados de aprendizaje:** {tema.get('Resultados de aprendizaje')}")
                st.write(f"**Bibliografía:** {tema.get('Bibliografía')}")
        elif isinstance(plan_json, dict):
            for i in range(len(plan_json) // 3):
                st.write(f"**Tema {i+1}:** {plan_json.get(f'tema_{i+1}')}")
                st.write(f"**Contenidos:** {plan_json.get(f'contenidos_{i+1}')}")
                st.write(f"**Indicador de logro:** {plan_json.get(f'indicador_logro_{i+1}')}")
                st.write(f"**Estrategias de evaluación:** {plan_json.get(f'estrategias_evaluacion_{i+1}')}")
                st.write(f"**Resultados de aprendizaje:** {plan_json.get(f'resultados_aprendizaje_{i+1}')}")
                st.write(f"**Bibliografía:** {plan_json.get(f'bibliografia_{i+1}')}")

        # Generar críticas y recomendaciones
        #critiques = analyze_and_critique_program(
        #    program={"objectives": program_text, "learning_outcomes": "", "indicators": ""}, 
        #   new_topic="Machine Learning en pronósticos de demanda", 
        #    teacher_comments=idea_profesor
        #)

        # Crear el PDF con las recomendaciones
        #create_pdf(critiques)

        #st.success("PDF con recomendaciones creado exitosamente.")
        #with open("recomendaciones_programa.pdf", "rb") as pdf_file:
        #   st.download_button(label="Descargar PDF", data=pdf_file, file_name="recomendaciones_programa.pdf")

    else:
        st.error("Por favor, sube el programa del curso.")