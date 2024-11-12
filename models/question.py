from pydantic import BaseModel
from typing import List


class QuestionAnswer(BaseModel):
    pregunta: str
    respuesta: str


class QuestionAnswerList(BaseModel):
    questions_answers: List[QuestionAnswer]
