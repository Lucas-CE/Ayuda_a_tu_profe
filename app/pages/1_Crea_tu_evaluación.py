import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import dotenv
import os
import PyPDF2
from markdown_pdf import MarkdownPdf, Section
from io import BytesIO
from pydantic import BaseModel
from typing import List


class QuestionAnswer(BaseModel):
    pregunta: str
    respuesta: str


class QuestionAnswerList(BaseModel):
    questions_answers: List[QuestionAnswer]


# Configuración de la página
st.set_page_config(
    page_title="Generador de Evaluaciones", page_icon="📝", layout="wide"
)

# Inicializar estados para edición
if "editing_question" not in st.session_state:
    st.session_state.editing_question = None
if "editing_answer" not in st.session_state:
    st.session_state.editing_answer = None
if "editing_alternatives" not in st.session_state:
    st.session_state.editing_alternatives = None
if "editing_section" not in st.session_state:
    st.session_state.editing_section = None


# Cargar variables de entorno y configurar el modelo
@st.cache_resource
def load_model():
    dotenv.load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    model = ChatOpenAI(openai_api_key=api_key, model="gpt-4o-mini")
    structured_llm = model.with_structured_output(QuestionAnswerList)
    return structured_llm


llm = load_model()

# Plantilla para el sistema
system_template_message = """
Eres un profesor experto en crear evaluaciones de la materia {topic}.

Basado en tu conocimiento y en la bibliografía:
{bibliography}

en las siguientes preguntas realizadas anteriormente:
{sample_questions}

tienes que crear una evaluación según las especificaciones dadas
por el profesor.

"""

comentarios_adicionales = """
Considera estos comentarios adicionales al crear las preguntas:
{comments}
"""

user_template_message = """
Crea {question_quantity} preguntas de tipo {question_type}
sobre el tema {topic} basandote en la bibliografía.
Las preguntas deben tener dificultad {difficulty}.
"""

output_desarrollo_template = """
El output debe ser un objeto JSON con la llave question_answers,
que tiene como valor una lista de objetos JSON con las llaves
- pregunta: la pregunta generada
- respuesta: la respuesta basada en la bibliografía

Ejemplo:
{{
    "question_answers": [
        {{"pregunta": "¿Cuál es la capital de Francia?", "respuesta": "París"}},
        {{"pregunta": "Compara la ventaja competitiva de Zara con la de otra empresa de retail de tu elección. ¿Qué diferencias o similitudes ves en sus enfoques estratégicos?", "respuesta": "Zara se distingue por su enfoque en la integración vertical y el control total sobre su cadena de suministro, lo que le permite minimizar los tiempos de producción y responder rápidamente a las tendencias del mercado. En contraste, H&M tiende a externalizar gran parte de su producción, lo que le permite mayor flexibilidad en la elección de proveedores, pero pierde control sobre los tiempos de entrega y la capacidad de respuesta rápida. Mientras Zara se centra en la eficiencia y la velocidad, H&M opta por reducir costos mediante la subcontratación."}}
        {{"pregunta": "En el contexto de búsqueda de textos expresados en espacios vectoriales, ¿por qué es útil la función de similitud coseno?", "respuesta": "La función de similitud coseno es útil en la búsqueda de textos expresados en espacios vectoriales porque mide la similitud entre dos vectores basándose en el ángulo entre ellos, en lugar de en su magnitud. Esto permite comparar textos de diferentes longitudes y normaliza la influencia de la magnitud de los vectores en la medida de similitud, lo que resulta en una comparación más precisa de la similitud semántica entre los textos."}}
    ]
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


# Función extraer preguntas y respuestas
def parse_question_jsons(questions_answers_list: List[QuestionAnswer]):
    questions = []
    for question_answer in questions_answers_list:
        questions.append(question_answer.model_dump())
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
            ("system", system_template_message + output_template),
            ("user", user_template_message),
        ]
    )
    chain = prompt_template | llm

    questions_json = chain.invoke(prompt_input)
    return parse_question_jsons(questions_json, question_type)


def toggle_edit_mode(question_idx, section):
    collection = (
        st.session_state.questions_selected
        if section == "selected"
        else st.session_state.questions_generated
    )
    question = collection[question_idx]

    if (
        st.session_state.editing_question == question_idx
        and st.session_state.editing_section == section
    ):
        st.session_state.editing_question = None
        st.session_state.editing_answer = None
        st.session_state.editing_alternatives = None
        st.session_state.editing_section = None
    else:
        st.session_state.editing_question = question_idx
        st.session_state.editing_answer = question["respuesta"]
        st.session_state.editing_section = section
        if "alternativas" in question:
            st.session_state.editing_alternatives = ", ".join(question["alternativas"])


def save_edits(question_idx, section):
    collection = (
        st.session_state.questions_selected
        if section == "selected"
        else st.session_state.questions_generated
    )
    question = collection[question_idx]

    # Usar keys específicas para cada sección
    question["pregunta"] = st.session_state.get(
        f"edit_question_{section}_{question_idx}", question["pregunta"]
    )
    question["respuesta"] = st.session_state.get(
        f"edit_answer_{section}_{question_idx}", question["respuesta"]
    )

    if "alternativas" in question:
        alternatives_text = st.session_state.get(
            f"edit_alternatives_{section}_{question_idx}", ""
        )
        question["alternativas"] = [alt.strip() for alt in alternatives_text.split(",")]

    st.session_state.editing_question = None
    st.session_state.editing_answer = None
    st.session_state.editing_alternatives = None
    st.session_state.editing_section = None


def show_card_question(question, idx, section):
    is_editing = (
        st.session_state.editing_question == idx
        and st.session_state.editing_section == section
    )

    # Crear un contenedor con borde y padding
    with st.container():
        # Primera fila: Pregunta y botones
        col1, col2, col3 = st.columns([3.4, 0.22, 0.22])

        with col1:
            if is_editing:
                st.text_input(
                    "Pregunta",
                    value=question["pregunta"],
                    key=f"edit_question_{section}_{idx}",
                )
            else:
                st.markdown(f"**Pregunta:** {question['pregunta']}")

        with col2:
            st.button(
                "✏️",
                key=f"edit_{section}_{idx}",
                on_click=toggle_edit_mode,
                args=(idx, section),
            )

        with col3:
            if is_editing:
                st.button(
                    "💾",
                    key=f"save_{section}_{idx}",
                    on_click=save_edits,
                    args=(idx, section),
                )

        # Segunda fila: Respuesta y alternativas
        if is_editing:
            st.text_area(
                "Respuesta",
                value=question["respuesta"],
                key=f"edit_answer_{section}_{idx}",
            )

            if "alternativas" in question:
                st.text_input(
                    "Alternativas (separadas por comas)",
                    value=", ".join(question["alternativas"]),
                    key=f"edit_alternatives_{section}_{idx}",
                )
        else:
            st.markdown(f"**Respuesta:** {question['respuesta']}")
            if "alternativas" in question:
                st.markdown(f"**Alternativas:** {', '.join(question['alternativas'])}")


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
    question_answer = f"Respuesta: {question['respuesta']}"
    if "alternativas" in question:
        alternatives = [
            f"Opción {chr(65+i)}: {alt}"
            for i, alt in enumerate(question["alternativas"])
        ]
        return "\n".join([question_title, question_answer] + alternatives)
    return "\n\n".join([question_title, question_answer])


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

difficulty = st.selectbox(
    "¿Qué tan difícil quieres que sean las preguntas?",
    ["Fácil", "Intermedio", "Difícil"],
)

extra_comments = st.text_area("Comentarios adicionales")

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
    and difficulty
):
    # Seleccionar el template de output
    complete_system_template_message = system_template_message

    if extra_comments:
        complete_system_template_message += "\n" + comentarios_adicionales.format(
            comments=extra_comments
        )

    if question_type == "Desarrollo":
        complete_system_template_message += "\n" + output_desarrollo_template
    elif question_type == "Alternativas":
        complete_system_template_message += "\n" + output_alternativas_template
    elif question_type == "Verdadero y Falso":
        complete_system_template_message = "\n" + output_verdadero_falso_template

    # Crear el prompt para LLM
    prompt_template = ChatPromptTemplate.from_messages(
        messages=[
            ("system", complete_system_template_message),
            ("user", user_template_message),
        ]
    )
    chain = prompt_template | llm

    # Crear el input para el modelo
    prompt_input = {
        "bibliography": bibliography_text,
        "sample_questions": sample_questions_text,
        "question_quantity": num_questions,
        "question_type": question_type,
        "difficulty": difficulty,
        "topic": topic,
    }

    # Generar las preguntas
    try:
        questions_json = chain.invoke(prompt_input)
        questions = parse_question_jsons(questions_json.questions_answers)
    except Exception as e:
        st.error(f"Error al generar las preguntas: {e}")
        st.text("Intentalo de nuevo.")
        questions = []

    # Agregar las preguntas generadas al estado
    st.session_state.questions_generated = questions


# Mostrar las preguntas generadas
if st.session_state.questions_generated:
    st.markdown("## Preguntas generadas:")
    st.markdown(" ")

    for idx, question in enumerate(st.session_state.questions_generated):
        col1, col2 = st.columns([0.5, 4])
        with col1:
            st.button(
                "Agregar",
                key=f"select_{idx}",
                on_click=select_question,
                args=(question,),
            )
        with col2:
            show_card_question(question, idx, "generated")
        st.markdown("---")  # Línea divisoria sutil

# Mostrar las preguntas seleccionadas
if st.session_state.questions_selected:
    st.markdown("## Preguntas seleccionadas:")
    st.markdown(" ")

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
            show_card_question(question, idx, "selected")
        st.markdown("---")  # Línea divisoria sutil

# Un solo botón para generar y descargar el PDF
if st.session_state.questions_selected:
    st.download_button(
        label="Descargar Pauta",
        data=markdown_test_to_pdf(st.session_state.questions_selected, topic),
        file_name=f"Prueba de {topic}.pdf",
        mime="application/pdf",
    )
