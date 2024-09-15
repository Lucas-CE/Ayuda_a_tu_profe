import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import SimpleJsonOutputParser
import dotenv
import os
import PyPDF2
from markdown_pdf import MarkdownPdf, Section
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


# Función para leer archivos PDF
def read_pdf(file):
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    for page_num in range(len(pdf_reader.pages)):
        text += pdf_reader.pages[page_num].extract_text()
    return text


def get_number_of_questions(json, type_question):
    json_len = len(json)
    if type_question == "Alternativas":
        return json_len // 4
    else:
        return json_len // 3


def parse_question_jsons(json, type_question):
    num_questions = get_number_of_questions(json, type_question)
    questions = []
    for i in range(num_questions):
        question = json[f"pregunta_{i + 1}"]
        bibliography = json[f"bibliografia_{i + 1}"]
        answer = json[f"respuesta_{i + 1}"]
        if type_question == "Alternativas":
            alternatives = json[f"alternativas_{i + 1}"]
            questions.append(
                {
                    "pregunta": question,
                    "bibliografia": bibliography,
                    "respuesta": answer,
                    "alternativas": alternatives,
                }
            )
        else:
            questions.append(
                {
                    "pregunta": question,
                    "bibliografia": bibliography,
                    "respuesta": answer,
                }
            )
    return questions


# Iniciar variables de estado
if "questions_generated" not in st.session_state:
    st.session_state.questions_generated = []
if "questions_selected" not in st.session_state:
    st.session_state.questions_selected = []


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
    questions = parse_question_jsons(questions_json, question_type)

    # Agregar las preguntas generadas al estado
    st.session_state.questions_generated = questions


def show_card_question(question):
    with st.expander(f"**{question['pregunta']}**"):
        st.write(f"Bibliografía: {question['bibliografia']}")
        st.write(f"Respuesta: {question['respuesta']}")
        if "alternativas" in question:
            st.write(f"Alternativas: {', '.join(question['alternativas'])}")


def select_question(question):
    st.session_state.questions_selected.append(question)
    st.session_state.questions_generated.remove(question)


def delete_question(question):
    st.session_state.questions_selected.remove(question)


# Mostrar las preguntas generadas
if st.session_state.questions_generated:
    st.markdown("### Preguntas generadas:")

    for idx, question in enumerate(st.session_state.questions_generated):
        col1, col2 = st.columns([1, 4])
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
        col1, col2 = st.columns([1, 4])
        with col1:
            st.button(
                "Eliminar",
                key=f"delete_{idx}",
                on_click=delete_question,
                args=(question,),
            )
        with col2:
            show_card_question(question)


def markdown_question_text(question):
    question_title = f"### {question['pregunta']}"
    question_bibliography = f"Bibliografía: {question['bibliografia']}"
    question_answer = f"Respuesta: {question['respuesta']}"
    if "alternativas" in question:
        a_option = f"Opción A: {question['alternativas'][0]}"
        b_option = f"Opción B: {question['alternativas'][1]}"
        c_option = f"Opción C: {question['alternativas'][2]}"
        d_option = f"Opción D: {question['alternativas'][3]}"
        return "\n".join(
            [
                question_title,
                question_bibliography,
                question_answer,
                a_option,
                b_option,
                c_option,
                d_option,
            ]
        )
    return "\n".join([question_title, question_bibliography, question_answer])


def markdown_test_text(selected_questions, topic):
    title = "# Prueba sobre " + topic
    questions = []
    for idx, question in enumerate(selected_questions):
        question_title = f"### Pregunta {idx + 1}"
        question_text = markdown_question_text(question)
        questions.append(question_title)
        questions.append(question_text)
    return "\n".join([title] + questions)


# Función para generar un PDF usando MarkdownPdf
def markdown_test_to_pdf(selected_questions, topic):
    markdown_content = markdown_test_text(selected_questions, topic)

    pdf = MarkdownPdf()
    section = Section(markdown_content, toc=False)
    pdf.add_section(section)

    # Guardar el PDF en un buffer en memoria
    pdf_output = BytesIO()
    pdf.save(pdf_output)
    pdf_output.seek(0)  # Volver al inicio del archivo en memoria
    return pdf_output


# Botón para generar y descargar el PDF
if st.button("Generar PDF"):
    pdf_output = markdown_test_to_pdf(st.session_state.questions_selected, topic)

    # Descargar el archivo PDF
    st.download_button(
        label="Descargar PDF",
        data=pdf_output,
        file_name="prueba.pdf",
        mime="application/pdf",
    )
