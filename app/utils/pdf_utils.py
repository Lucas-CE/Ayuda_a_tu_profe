import PyPDF2
from io import BytesIO
from markdown_pdf import MarkdownPdf, Section
import streamlit as st
from models.question import (
    DevelopmentQuestion,
    MultipleChoiceQuestion,
    TrueFalseQuestion,
)
from typing import Union


@st.cache_data
def extract_text_from_pdf(file: BytesIO) -> str:
    """
    Lee el contenido de un archivo PDF y devuelve el texto extraído.

    Args:
        file (file): Archivo PDF.
    Returns:
        str: Texto extraído del archivo PDF.

    Example:
        >>> with open('documento.pdf', 'rb') as pdf_file:
        ...     contenido = extract_text_from_pdf(BytesIO(pdf_file.read()))
        >>> print(contenido)
        'Este es el texto extraído del PDF...'
    """
    pdf_reader = PyPDF2.PdfReader(file)
    return " ".join(page.extract_text() for page in pdf_reader.pages)


def format_question_to_markdown(
    question: Union[DevelopmentQuestion, MultipleChoiceQuestion, TrueFalseQuestion]
) -> str:
    """
    Genera el texto Markdown para una pregunta.

    Args:
        question (dict): Pregunta con estructura específica.
    Returns:
        str: Texto Markdown para una pregunta.

    Example:
        >>> pregunta = {
        ...     'pregunta': '¿Cuál es la capital de Francia?',
        ...     'respuesta': 'París',
        ...     'alternativas': ['Londres', 'París', 'Madrid', 'Roma']
        ... }
        >>> print(format_question_to_markdown(pregunta))
        ### ¿Cuál es la capital de Francia?
        Respuesta: París
        Opción A: Londres
        Opción B: París
        Opción C: Madrid
        Opción D: Roma
    """
    question_title = f"### {question.pregunta}"
    question_answer = f"Respuesta: {question.respuesta}"
    if type(question).__name__ == "MultipleChoiceQuestion":
        alternatives = [
            f"Opción {chr(65+i)}: {alt}" for i, alt in enumerate(question.alternativas)
        ]
        return "\n\n".join([question_title, question_answer] + alternatives)
    return "\n\n".join([question_title, question_answer])


def generate_test_markdown(selected_questions: list, topic: str) -> str:
    """
    Genera el texto Markdown para una prueba.

    Args:
        selected_questions (list): Lista de preguntas seleccionadas.
        topic (str): Tema de la prueba.
    Returns:
        str: Texto Markdown para una prueba.

    Example:
        >>> preguntas = [
        ...     {
        ...         'pregunta': '¿Cuál es la capital de Francia?',
        ...         'respuesta': 'París'
        ...     }
        ... ]
        >>> print(generate_test_markdown(preguntas, 'Geografía'))
        # Prueba sobre Geografía
        ### Pregunta 1
        ### ¿Cuál es la capital de Francia?
        Respuesta: París
    """
    title = f"# Prueba sobre {topic}"
    questions = []
    for idx, question in enumerate(selected_questions):
        question_title = f"### Pregunta {idx + 1}"
        question_text = format_question_to_markdown(question)
        questions.extend([question_title, question_text])
    return "\n".join([title] + questions)


def convert_test_to_pdf(selected_questions: list, topic: str) -> BytesIO:
    """
    Genera un archivo PDF a partir del texto Markdown de una prueba.

    Args:
        selected_questions (list): Lista de preguntas seleccionadas.
        topic (str): Tema de la prueba.
    Returns:
        BytesIO: Archivo PDF en formato BytesIO.

    Example:
        >>> preguntas = [
        ...     {
        ...         'pregunta': '¿Cuál es la capital de Francia?',
        ...         'respuesta': 'París'
        ...     }
        ... ]
        >>> pdf_bytes = convert_test_to_pdf(preguntas, 'Geografía')
        >>> with open('prueba.pdf', 'wb') as f:
        ...     f.write(pdf_bytes.getvalue())
    """
    markdown_content = generate_test_markdown(selected_questions, topic)
    pdf = MarkdownPdf()
    section = Section(markdown_content, toc=False)
    pdf.add_section(section)
    pdf_output = BytesIO()
    pdf.save(pdf_output)
    pdf_output.seek(0)
    return pdf_output
