"""
Schemas for helpers.
"""

import dataclasses
import datetime
import enum
import urllib.parse
import uuid

import pydantic

from api import errors, models


class TokenData(pydantic.BaseModel):
    """
    Schema for token data.
    """

    sub: str
    aud: str
    exp: datetime.datetime
    nbf: datetime.datetime
    iat: datetime.datetime
    scopes: list[str]


class ImportData(pydantic.BaseModel):
    """
    Schema related to all import data
    """

    url: pydantic.AnyHttpUrl
    key_relation: dict[str, str]


class ListSchema(pydantic.BaseModel):
    """
    Default list schema for list resources endpoints.
    """

    page_size: int = pydantic.Field(10, ge=-1, le=100)
    page: int = pydantic.Field(1, ge=1, le=1000)
    q: str | None = None

    @pydantic.validator("q")
    @classmethod
    def prevent_none(cls, q: str | None) -> str | None:
        """
        Validator to ensure that, if the field is sent, it's not None.
        """
        if q and q.strip() != "":
            if len(q) < 3:
                raise errors.FieldShouldBeLenghtier(field="q", min_length=3)
            return urllib.parse.unquote(q)
        return None


@dataclasses.dataclass
class AnalyticalResult:  # pylint: disable=too-many-instance-attributes
    """
    Result data to analytical database.
    """

    school_uuid: uuid.UUID
    school_name: str
    school_city: str
    school_state: str
    school_region: str | None
    school_county: str
    class_uuid: uuid.UUID
    class_name: str
    class_grade: str
    student_uuid: uuid.UUID
    student_customer_id: str | None
    student_name: str
    exam_uuid: uuid.UUID
    exam_name: str
    exam_grade: str
    exam_start_date: datetime.datetime
    exam_end_date: datetime.datetime
    question_uuid: uuid.UUID
    question_words: list[str]
    question_amount_words: int
    response_words: list[str]
    response_amount_hits: int
    response_timestamp: datetime.datetime
    user_rating: models.UserRating | None


class ImportType(enum.StrEnum):
    """
    Enum for type of import
    """

    USER = "USER"
    ORGANIZATION = "ORGANIZATION"
    GROUP = "GROUP"
