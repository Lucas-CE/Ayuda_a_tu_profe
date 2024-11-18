import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from utils.pdf_utils import (
    extract_text_from_pdf,
    convert_test_to_pdf,
    convert_test_to_pdf_without_answers,
)
from models.question import (
    DevelopmentQuestionList,
    MultipleChoiceQuestionList,
    TrueFalseQuestionList,
    DevelopmentQuestion,
    MultipleChoiceQuestion,
    TrueFalseQuestion,
)
from typing import Union

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
    api_key = st.secrets["OPENAI_API_KEY"]
    model = ChatOpenAI(
        openai_api_key=api_key,
        model="gpt-4o-mini",
        temperature=1,
    )
    return model


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
Genera preguntas de desarrollo.
El output debe ser un objeto JSON con la siguiente estructura:
{{
    "list_questions_answers": {{
        "questions_answers": [
            {{"pregunta": "¿Cuál es la capital de Francia?", "respuesta": "París"}},
            {{"pregunta": "Explica el proceso de fotosíntesis", "respuesta": "La fotosíntesis es..."}}
        ]
    }}
}}
"""

output_alternativas_template = """
Genera preguntas de alternativas.
El output debe ser un objeto JSON con la siguiente estructura:
{{
    "list_questions_answers": {{
        "questions_answers": [
            {{
                "pregunta": "¿Cuál es la capital de Francia?",
                "respuesta": "París",
                "alternativas": ["París", "Londres", "Berlín", "Madrid", "Roma"]
            }}
        ]
    }}
}}
"""

output_verdadero_falso_template = """
Genera preguntas de verdadero o falso.
El output debe ser un objeto JSON con la siguiente estructura:
{{
    "list_questions_answers": {{
        "questions_answers": [
            {{"pregunta": "París es la capital de Francia", "respuesta": "Verdadero"}},
            {{"pregunta": "Londres es la capital de Francia", "respuesta": "Falso"}}
        ]
    }}
}}
"""


# Función extraer preguntas y respuestas
def parse_question_jsons(
    questions_answers_list: (
        DevelopmentQuestionList | MultipleChoiceQuestionList | TrueFalseQuestionList
    ),
):
    return questions_answers_list.questions_answers


def toggle_edit_mode(question_idx, section):
    collection = (
        st.session_state.questions_selected
        if section == "selected"
        else st.session_state.questions_generated
    )
    question_answer: Union[
        DevelopmentQuestion, MultipleChoiceQuestion, TrueFalseQuestion
    ] = collection[question_idx]

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
        st.session_state.editing_answer = question_answer.respuesta
        st.session_state.editing_section = section
        if isinstance(question_answer, MultipleChoiceQuestion):
            st.session_state.editing_alternatives = ", ".join(
                question_answer.alternativas
            )


def save_edits(question_idx, section):
    collection = (
        st.session_state.questions_selected
        if section == "selected"
        else st.session_state.questions_generated
    )
    question = collection[question_idx]

    # Usar keys específicas para cada sección
    question.pregunta = st.session_state.get(
        f"edit_question_{section}_{question_idx}", question.pregunta
    )
    question.respuesta = st.session_state.get(
        f"edit_answer_{section}_{question_idx}", question.respuesta
    )

    if isinstance(question, MultipleChoiceQuestion):
        alternatives_text = st.session_state.get(
            f"edit_alternatives_{section}_{question_idx}", ""
        )
        question.alternativas = [alt.strip() for alt in alternatives_text.split(",")]

    st.session_state.editing_question = None
    st.session_state.editing_answer = None
    st.session_state.editing_alternatives = None
    st.session_state.editing_section = None


def show_card_question(
    question_answer: Union[
        DevelopmentQuestion, MultipleChoiceQuestion, TrueFalseQuestion
    ],
    idx: int,
    section: str,
):
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
                    value=question_answer.pregunta,
                    key=f"edit_question_{section}_{idx}",
                )
            else:
                st.markdown(f"**Pregunta:** {question_answer.pregunta}")

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
                value=question_answer.respuesta,
                key=f"edit_answer_{section}_{idx}",
            )

            if type(question_answer).__name__ == "MultipleChoiceQuestion":
                st.text_input(
                    "Alternativas (separadas por comas)",
                    value=", ".join(question_answer.alternativas),
                    key=f"edit_alternatives_{section}_{idx}",
                )
        else:
            st.markdown(f"**Respuesta:** {question_answer.respuesta}")
            if type(question_answer).__name__ == "MultipleChoiceQuestion":
                st.markdown("**Alternativas:**")
                for alternative in question_answer.alternativas:
                    st.markdown(f"- {alternative}")


# Funciones para seleccionar y eliminar preguntas
def select_question(question):
    if "questions_selected" not in st.session_state:
        st.session_state.questions_selected = []
    st.session_state.questions_selected.append(question)
    st.session_state.questions_generated.remove(question)


def delete_question(question):
    st.session_state.questions_selected.remove(question)


# Iniciar variables de estado
if "questions_generated" not in st.session_state:
    st.session_state.questions_generated = []
if "questions_selected" not in st.session_state:
    st.session_state.questions_selected = []


# Interfaz de usuario
st.title("Generador de Evaluaciones 📝")

st.markdown(
    """
    Esta herramienta te permite generar preguntas de evaluación para tu curso.

    Recomendaciones:
    - Al generar preguntas las puedes editar para que se ajusten a tu
    preferencia.
    - Si no te gustaron las preguntas generadas, puedes generarlas de nuevo,
    y aumentar el número de preguntas.
    - Luego de generar preguntas, puedes modificar comentarios adicionales
    y generar nuevas preguntas para que las preguntas se ajusten mejor a tus
    necesidades.
    """
)

# Selección de parámetros
topic = st.text_input("Ingresa el tema de la evaluación")

num_questions = st.number_input(
    "¿Cuántas preguntas quieres generar? (Entre 1 y 20)",
    min_value=1,
    max_value=20,
    step=1,
)
question_type = st.selectbox(
    "¿Qué tipo de preguntas quieres generar?",
    ["Alternativas", "Desarrollo", "Verdadero y Falso"],
)

uploaded_bibliography = st.file_uploader(
    "Sube una clase en la que quieras basar las preguntas", type=["pdf"]
)
uploaded_sample_questions = st.file_uploader(
    "Sube preguntas de otra prueba que hayas realizado en el curso (opcional)",
    type=["pdf"],
)

difficulty = st.selectbox(
    "¿Qué tan difícil quieres que sean las preguntas?",
    ["Fácil", "Intermedio", "Difícil"],
)

extra_comments = st.text_area(
    "Comentarios adicionales (cualquier especificación acerca de las preguntas a crear)"
)

# Leer la bibliografía y preguntas tipo subidas
bibliography_text = ""
sample_questions_text = ""

if uploaded_bibliography:
    bibliography_text = extract_text_from_pdf(uploaded_bibliography)

if uploaded_sample_questions:
    sample_questions_text = extract_text_from_pdf(uploaded_sample_questions)

if uploaded_bibliography and uploaded_sample_questions:
    st.success("Archivos cargados correctamente.")

# Generar preguntas
if (
    st.button("Generar preguntas nuevas")
    and uploaded_bibliography
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
        structured_llm = llm.with_structured_output(DevelopmentQuestionList)
    elif question_type == "Alternativas":
        complete_system_template_message += "\n" + output_alternativas_template
        structured_llm = llm.with_structured_output(MultipleChoiceQuestionList)
    elif question_type == "Verdadero y Falso":
        complete_system_template_message += "\n" + output_verdadero_falso_template
        structured_llm = llm.with_structured_output(TrueFalseQuestionList)
    # Crear el prompt para LLM
    prompt_template = ChatPromptTemplate.from_messages(
        messages=[
            ("system", complete_system_template_message),
            ("user", user_template_message),
        ]
    )
    chain = prompt_template | structured_llm

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
        questions = parse_question_jsons(questions_json)
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

    for idx, question_answer in enumerate(st.session_state.questions_generated):
        col1, col2 = st.columns([0.5, 4])
        with col1:
            st.button(
                "Agregar",
                key=f"select_{idx}",
                on_click=select_question,
                args=(question_answer,),
            )
        with col2:
            show_card_question(question_answer, idx, "generated")
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
        data=convert_test_to_pdf(st.session_state.questions_selected, topic),
        file_name=f"Prueba de {topic}.pdf",
        mime="application/pdf",
    )
    st.download_button(
        label="Descargar Pauta sin respuestas",
        data=convert_test_to_pdf_without_answers(
            st.session_state.questions_selected, topic
        ),
        file_name=f"Prueba de {topic} sin respuestas.pdf",
        mime="application/pdf",
    )
