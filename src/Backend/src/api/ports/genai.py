"""
Module containing storage abstract.
"""

import abc
import typing

from api import models


class GenAI(abc.ABC):
    """
    Generative AI abstract
    """

    @abc.abstractmethod
    def generate_words(
        self,
        qty_words: str,
        question_type: models.QuestionType,
        block_words: list[str] | None = None,
    ) -> str:
        """
        Method genarates x amount of words.
        """

    @abc.abstractmethod
    def generate_multiple_choice(
        self,
        qty: int,
        text: str | None,
        user_input: str | None,
        block_questions: list[str] | None = None,
    ) -> dict[str, typing.Any]:
        """
        Method genarates a multiple choice question.
        """

    @abc.abstractmethod
    def generate_text(self, subject: str = "infantil") -> str:
        """
        Method genarates a readable text.
        """

    @abc.abstractmethod
    def generate_question(
        self,
        question_type: models.QuestionType,
        text_data: str | None,
        user_input: str | None,
        block_questions: list[str] | None,
        question_theme: models.QuestionTheme | None = None,
    ) -> str:
        """
        Method that generates a basic question
        """

    @abc.abstractmethod
    def evaluate_test(
        self,
        question_type: models.QuestionType,
        text_data: str,
        tts_data: str,
        question_theme: models.QuestionTheme | None = None,
    ) -> tuple[bool, str]:
        """
        Method that evaluate user answer.
        """

    @abc.abstractmethod
    def get_exam_feedback(self, questions: list[typing.Any]) -> str:
        """
        Method that generates a feedback for the entire exam
        """

    @abc.abstractmethod
    async def index_document(
        self, doc_id: str, text: str, metadata: dict[str, typing.Any] | None = None
    ) -> None:
        """
        Index a document (generate embeddings and store vectors in the vector store).
        """

    @abc.abstractmethod
    async def delete_document(self, doc_id: str) -> None:
        """
        Delete a document and all its chunks from the vector store.
        """

    @abc.abstractmethod
    async def query_kb(
        self, query_text: str, limit: int = 5
    ) -> list[dict[str, typing.Any]]:
        """
        Query the pedagogical knowledge base for recommendations.
        """

    @abc.abstractmethod
    async def generate_description(self, text: str) -> str:
        """
        Generate a brief description/summary of the given document text.
        """

