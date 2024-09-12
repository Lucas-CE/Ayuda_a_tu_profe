import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import SimpleJsonOutputParser
import dotenv
import os
import PyPDF2
from io import BytesIO

st.set_page_config(
    page_title="Generador de Evaluaciones",
    page_icon="📝",
)

# Cargar variables de entorno
dotenv.load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(openai_api_key=api_key, model="gpt-4o-mini")

# Plantilla para el sistema
system_template_message = """
Eres un profesor experto en crear evaluaciones de la materia {topic}.
"""

user_template_message = """
Basado en la siguiente bibliografía:
{bibliography}

en las siguientes preguntas realizadas anteriormente:
{sample_questions}

Crea {question_quantity} preguntas de tipo {question_type}
sobre el tema {topic}, y que las respuestas sean {directness}
a partir de la bibliografía.
"""

output_desarrollo_template = """
El output debe ser un objeto JSON con las llaves
- pregunta_i: la pregunta generada
- bibliografia_i: la sección relevante de la bibliografía
- respuesta_i: la respuesta basada en la bibliografía

Ejemplo:
{{
    "pregunta_1": "¿Cuál es la capital de Francia?",
    "bibliografia_1": "la capital de Francia es París",
    "respuesta_1": "París",
    "pregunta_2": "¿Cuál es la capital de España?",
    "bibliografia_2": "la capital de España es Madrid",
    "respuesta_2": "Madrid",
}}
"""

output_alternativas_template = """
El output debe ser un objeto JSON con las llaves
- pregunta_i: la pregunta generada
- bibliografia_i: la sección relevante de la bibliografía
- respuesta_i: la respuesta basada en la bibliografía
- alternativas_i: las alternativas de respuesta

Ejemplo:
{
    "pregunta_1": "¿Cuál es la capital de Francia?",
    "bibliografia_1": "la capital de Francia es París",
    "respuesta_1": "París",
    "alternativas_1": ["París", "Madrid", "Londres", "Berlín"],
    "pregunta_2": "¿Cuál es la capital de España?",
    "bibliografia_2": "la capital de España es Madrid",
    "respuesta_2": "Madrid",
    "alternativas_2": ["París", "Madrid", "Londres", "Berlín"],
}
"""

output_verdadero_falso_template = """
El output debe ser un objeto JSON con las llaves
- pregunta_i: la pregunta generada
- bibliografia_i: la sección relevante de la bibliografía
- respuesta_i: la respuesta basada en la bibliografía

Ejemplo:
{
    "pregunta_1": "¿La capital de Francia es París?",
    "bibliografia_1": "la capital de Francia es París",
    "respuesta_1": "Verdadero",
    "pregunta_2": "¿La capital de España es Madrid?",
    "bibliografia_2": "la capital de España es Madrid",
    "respuesta_2": "Verdadero",
}
"""

# Iniciar variables de estado
if "questions_generated" not in st.session_state:
    st.session_state.questions_generated = []
if "questions_selected" not in st.session_state:
    st.session_state.questions_selected = []


# Función para leer archivos PDF
def read_pdf(file):
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    for page_num in range(len(pdf_reader.pages)):
        text += pdf_reader.pages[page_num].extract_text()
    return text


# Interfaz de Streamlit
st.markdown("# Crea tu evaluación")

# Selección de parámetros
topic = st.text_input("Ingresa el tema de la evaluación")

num_questions = st.number_input(
    "Número de preguntas", min_value=1, max_value=20, step=1
)
question_type = st.selectbox(
    "Tipo de preguntas", ["Alternativas", "Desarrollo", "Verdadero y Falso"]
)

uploaded_bibliography = st.file_uploader("Sube la bibliografía (PDF)", type=["pdf"])
uploaded_sample_questions = st.file_uploader(
    "Sube preguntas anteriores (PDF)", type=["pdf"]
)

directness = st.selectbox(
    "¿Qué tan directas deben ser las respuestas a partir de la bibliografía?",
    ["Muy directas", "Semi directas", "No directas"],
)

# Leer la bibliografía y preguntas tipo subidas
bibliography_text = ""
sample_questions_text = ""

if uploaded_bibliography:
    bibliography_text = read_pdf(uploaded_bibliography)

if uploaded_sample_questions:
    sample_questions_text = read_pdf(uploaded_sample_questions)

if uploaded_bibliography and uploaded_sample_questions:
    st.success("Archivos cargados correctamente.")

# Generar preguntas
if (
    st.button("Generar preguntas")
    and uploaded_bibliography
    and uploaded_sample_questions
):
    # Limpiar el estado
    st.session_state.questions_generated = []
    # Seleccionar el template de output
    complete_user_template_message = ""
    if question_type == "Desarrollo":
        complete_user_template_message = (
            user_template_message + output_desarrollo_template
        )
    elif question_type == "Alternativas":
        complete_user_template_message = (
            user_template_message + output_alternativas_template
        )
    elif question_type == "Verdadero y Falso":
        complete_user_template_message = (
            user_template_message + output_verdadero_falso_template
        )
    print("Template:", complete_user_template_message)
    # Crear el prompt para LLM
    prompt_template = ChatPromptTemplate.from_messages(
        messages=[
            ("system", system_template_message),
            ("user", complete_user_template_message),
        ]
    )
    chain = prompt_template | llm | SimpleJsonOutputParser()

    # Crear el input para el modelo
    prompt_input = {
        "bibliography": bibliography_text,
        "sample_questions": sample_questions_text,
        "question_quantity": num_questions,
        "question_type": question_type,
        "directness": directness,
        "topic": topic,
    }

    # Generar las preguntas
    questions_json = chain.invoke(prompt_input)
    st.session_state.questions_generated = questions_json

print("Preguntas generadas:", st.session_state.questions_generated)
# Mostrar las preguntas generadas como "cards"
if st.session_state.questions_generated:
    st.markdown("### Preguntas generadas:")
    # Mostrar cada pregunta con su respuesta y bibliografía
    for question in st.session_state.questions_generated:
        with st.expander(f"**{question['pregunta']}**"):
            st.write(f"Bibliografía: {question['bibliografia']}")
            st.write(f"Respuesta: {question['respuesta']}")
            if "alternativas" in question:
                st.write(f"Alternativas: {', '.join(question['alternativas'])}")

    # Seleccionar preguntas generadas
    selected_questions = st.multiselect(
        "Selecciona las preguntas que deseas agregar al documento final",
        options=[q["pregunta"] for q in st.session_state.questions_generated],
    )


# Función para generar el PDF
def create_pdf(content):
    pdf_writer = PyPDF2.PdfWriter()
    packet = BytesIO()

    # Crear un archivo PDF en memoria
    pdf_writer.add_blank_page(width=210, height=297)  # A4 dimensions
    packet.seek(0)

    # Escribir el contenido en el archivo
    for page_content in content:
        page = pdf_writer.pages[0]
        page.merge_text(page_content)

    # Guardar el archivo en BytesIO
    pdf_writer.write(packet)
    packet.seek(0)
    return packet


# Botón para generar PDFs
if st.button("Generar PDF") and selected_questions:
    # Generar el contenido de las preguntas seleccionadas
    preguntas_pdf_content = []
    respuestas_pdf_content = []

    for question in st.session_state.questions_generated:
        if question["pregunta"] in selected_questions:
            preguntas_pdf_content.append(f"Pregunta: {question['pregunta']}\n")
            respuestas_pdf_content.append(
                f"Pregunta: {question['pregunta']}\nRespuesta: {question['respuesta']}\n"
            )

    # Crear PDFs para preguntas y respuestas
    preguntas_pdf = create_pdf(preguntas_pdf_content)
    respuestas_pdf = create_pdf(respuestas_pdf_content)

    # Botones para descargar los PDFs
    st.download_button(
        "Descargar preguntas",
        preguntas_pdf,
        file_name="preguntas.pdf",
        mime="application/pdf",
    )
    st.download_button(
        "Descargar pauta", respuestas_pdf, file_name="pauta.pdf", mime="application/pdf"
    )
