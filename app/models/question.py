from pydantic import BaseModel
from typing import List, Literal, Union


class DevelopmentQuestion(BaseModel):
    pregunta: str
    respuesta: str


class MultipleChoiceQuestion(BaseModel):
    pregunta: str
    respuesta: str
    alternativas: List[str]


class TrueFalseQuestion(BaseModel):
    pregunta: str
    respuesta: Literal["Verdadero", "Falso"]


class DevelopmentQuestionList(BaseModel):
    questions_answers: List[DevelopmentQuestion]


class MultipleChoiceQuestionList(BaseModel):
    questions_answers: List[MultipleChoiceQuestion]


class TrueFalseQuestionList(BaseModel):
    questions_answers: List[TrueFalseQuestion]


class QuestionList(BaseModel):
    list_questions_answers: (
        DevelopmentQuestionList | MultipleChoiceQuestionList | TrueFalseQuestionList
    )
