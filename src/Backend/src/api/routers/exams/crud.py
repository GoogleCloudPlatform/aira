"""
Module containing crud actions for exams
"""

from api import models, ports
from api.helpers import util

from . import schemas


async def build_question_phrase(
    question: schemas.Question,
    speech: ports.SpeechToText,
) -> str:
    """
    Abstract build question phrase to be used by patch and create exam.
    """
    text_list: list[str] = []
    match question.type:
        case models.QuestionType.PHRASES:
            phrase_list = (
                question.data.split(". ")
                if ". " in question.data
                else question.data.split(".")
            )
            for phrase in phrase_list:
                text_list.extend(util.words_recursion(phrase))
        case models.QuestionType.WORDS | models.QuestionType.COMPLEX_WORDS:
            text_list = question.data.split(" ")
    phrases = [{"value": text, "boost": 20} for text in text_list]
    phrase_set_id = await speech.create_phrase_set(phrases)
    phrase_id = phrase_set_id.split("/")[-1]
    return phrase_id
