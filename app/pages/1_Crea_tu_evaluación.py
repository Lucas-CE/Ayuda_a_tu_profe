import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import SimpleJsonOutputParser
import dotenv
import os
import PyPDF2
from markdown_pdf import MarkdownPdf, Section
from io import BytesIO

# COSAS A MEJORAR
# - Agregar métodos de feedback para preguntas generadas
# - Desarrollo: existen preguntas de desarrollo y otras aplicadas como calculos
# - Agregar parámetro de cuánto tiempo se tiene para responder cada pregunta
# - Agregar espacio para agregar comentarios a la generación de preguntas

# Configuración de la página
st.set_page_config(
    page_title="Generador de Evaluaciones", page_icon="📝", layout="wide"
)


# Cargar variables de entorno y configurar el modelo
@st.cache_resource
def load_model():
    dotenv.load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    return ChatOpenAI(openai_api_key=api_key, model="gpt-4o-mini")


llm = load_model()

# Plantilla para el sistema
system_template_message = """
Eres un profesor experto en crear evaluaciones de la materia {topic}.
"""

user_template_message = """
Basado en tu conocimiento y en la siguiente bibliografía:
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
{{
    "pregunta_1": "¿Cuál es la capital de Francia?",
    "bibliografia_1": "la capital de Francia es París",
    "respuesta_1": "París",
    "alternativas_1": ["París", "Madrid", "Londres", "Berlín"],
    "pregunta_2": "¿Cuál es la capital de España?",
    "bibliografia_2": "la capital de España es Madrid",
    "respuesta_2": "Madrid",
    "alternativas_2": ["París", "Madrid", "Londres", "Berlín"],
}}
"""

output_verdadero_falso_template = """
El output debe ser un objeto JSON con las llaves
- pregunta_i: la pregunta generada
- bibliografia_i: la sección relevante de la bibliografía
- respuesta_i: la respuesta basada en la bibliografía

Ejemplo:
{{
    "pregunta_1": "¿La capital de Francia es París?",
    "bibliografia_1": "la capital de Francia es París",
    "respuesta_1": "Verdadero",
    "pregunta_2": "¿La capital de España es Madrid?",
    "bibliografia_2": "la capital de España es Madrid",
    "respuesta_2": "Verdadero",
}}
"""


# Función para leer archivos PDF
@st.cache_data
def read_pdf(file):
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text


# Función para analizar las preguntas JSON
def parse_question_jsons(json, type_question):
    num_questions = len(json) // (4 if type_question == "Alternativas" else 3)
    questions = []
    for i in range(num_questions):
        question = {
            "pregunta": json[f"pregunta_{i + 1}"],
            "bibliografia": json[f"bibliografia_{i + 1}"],
            "respuesta": json[f"respuesta_{i + 1}"],
        }
        if type_question == "Alternativas":
            question["alternativas"] = json[f"alternativas_{i + 1}"]
        questions.append(question)
    return questions


# Función para generar preguntas
@st.cache_data
def generate_questions(prompt_input, question_type):
    output_template = {
        "Desarrollo": output_desarrollo_template,
        "Alternativas": output_alternativas_template,
        "Verdadero y Falso": output_verdadero_falso_template,
    }[question_type]

    prompt_template = ChatPromptTemplate.from_messages(
        [
            ("system", system_template_message),
            ("user", user_template_message + output_template),
        ]
    )
    chain = prompt_template | llm | SimpleJsonOutputParser()

    questions_json = chain.invoke(prompt_input)
    return parse_question_jsons(questions_json, question_type)


def show_card_question(question):
    with st.expander(f"**{question['pregunta']}**"):
        st.write(f"Bibliografía: {question['bibliografia']}")
        st.write(f"Respuesta: {question['respuesta']}")
        if "alternativas" in question:
            st.write(f"Alternativas: {', '.join(question['alternativas'])}")


# Funciones para seleccionar y eliminar preguntas
def select_question(question):
    if "questions_selected" not in st.session_state:
        st.session_state.questions_selected = []
    st.session_state.questions_selected.append(question)
    st.session_state.questions_generated.remove(question)


def delete_question(question):
    st.session_state.questions_selected.remove(question)


# Funciones para generar el texto Markdown y PDF
def markdown_question_text(question):
    question_title = f"### {question['pregunta']}"
    question_bibliography = f"Bibliografía: {question['bibliografia']}"
    question_answer = f"Respuesta: {question['respuesta']}"
    if "alternativas" in question:
        alternatives = [
            f"Opción {chr(65+i)}: {alt}"
            for i, alt in enumerate(question["alternativas"])
        ]
        return "\n".join(
            [question_title, question_bibliography, question_answer] + alternatives
        )
    return "\n\n".join([question_title, question_bibliography, question_answer])


def markdown_test_text(selected_questions, topic):
    title = f"# Prueba sobre {topic}"
    questions = []
    for idx, question in enumerate(selected_questions):
        question_title = f"### Pregunta {idx + 1}"
        question_text = markdown_question_text(question)
        questions.extend([question_title, question_text])
    return "\n".join([title] + questions)


def markdown_test_to_pdf(selected_questions, topic):
    markdown_content = markdown_test_text(selected_questions, topic)
    pdf = MarkdownPdf()
    section = Section(markdown_content, toc=False)
    pdf.add_section(section)
    pdf_output = BytesIO()
    pdf.save(pdf_output)
    pdf_output.seek(0)
    return pdf_output


# Iniciar variables de estado
if "questions_generated" not in st.session_state:
    st.session_state.questions_generated = []
if "questions_selected" not in st.session_state:
    st.session_state.questions_selected = []


# Interfaz de usuario
st.title("Generador de Evaluaciones 📝")

# Selección de parámetros
topic = st.text_input("Ingresa el tema de la evaluación")

num_questions = st.number_input(
    "Número de preguntas", min_value=1, max_value=10, step=1
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
    and topic
    and num_questions
    and question_type
    and directness
):
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
        
    # Generar las preguntas
    try:
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

        questions_json = chain.invoke(prompt_input)
        questions = parse_question_jsons(questions_json, question_type)
    except Exception as e:
        st.error(f"Error al generar las preguntas: {e}")
        st.text("Intentalo de nuevo.")
        questions = []

    # Agregar las preguntas generadas al estado
    st.session_state.questions_generated = questions


# Mostrar las preguntas generadas
if st.session_state.questions_generated:
    st.markdown("### Preguntas generadas:")

    for idx, question in enumerate(st.session_state.questions_generated):
        col1, col2 = st.columns([0.5, 4])
        with col1:
            # Botón para seleccionar la pregunta
            st.button(
                "Agregar",
                key=f"select_{idx}",
                on_click=select_question,
                args=(question,),
            )
        with col2:
            show_card_question(question)

# Mostrar las preguntas seleccionadas
if st.session_state.questions_selected:
    st.markdown("### Preguntas seleccionadas:")

    for idx, question in enumerate(st.session_state.questions_selected):
        col1, col2 = st.columns([0.5, 4])
        with col1:
            st.button(
                "Eliminar",
                key=f"delete_{idx}",
                on_click=delete_question,
                args=(question,),
            )
        with col2:
            show_card_question(question)

# Un solo botón para generar y descargar el PDF
if st.session_state.questions_selected:
    st.download_button(
        label="Descargar PDF",
        data=markdown_test_to_pdf(st.session_state.questions_selected, topic),
        file_name=f"Prueba de {topic}.pdf",
        mime="application/pdf",
    )
