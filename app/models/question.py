from pydantic import BaseModel
from typing import List, Literal


class DevelopmentQuestion(BaseModel):
    """
    Clase para representar una pregunta de desarrollo.
    """
    pregunta: str
    respuesta: str


class MultipleChoiceQuestion(BaseModel):
    """
    Clase para representar una pregunta de opción múltiple.
    """
    pregunta: str
    respuesta: str
    alternativas: List[str]


class TrueFalseQuestion(BaseModel):
    """
    Clase para representar una pregunta de verdadero o falso.
    """
    pregunta: str
    respuesta: Literal["Verdadero", "Falso"]


class DevelopmentQuestionList(BaseModel):
    """
    Clase para representar una lista de preguntas de desarrollo.
    """
    questions_answers: List[DevelopmentQuestion]


class MultipleChoiceQuestionList(BaseModel):
    """
    Clase para representar una lista de preguntas de opción múltiple.
    """
    questions_answers: List[MultipleChoiceQuestion]


class TrueFalseQuestionList(BaseModel):
    """
    Clase para representar una lista de preguntas de verdadero o falso.
    """
    questions_answers: List[TrueFalseQuestion]
