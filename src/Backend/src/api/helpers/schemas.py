"""
Schemas for helpers.
"""
import dataclasses
import datetime
import uuid

import pydantic


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


class ListSchema(pydantic.BaseModel):
    """
    Default list schema for list resources endpoints.
    """

    page_size: int = pydantic.Field(10, ge=-1, le=100)
    page: int = pydantic.Field(1, ge=1, le=100)
    q: str | None = None

    @pydantic.validator("q")
    @classmethod
    def prevent_none(cls, q: str | None) -> str | None:
        """
        Validator to ensure that, if the field is sent, it's not None.
        """
        if q:
            if q.strip() != "" and len(q) < 3:
                return (  # pylint: disable=fixme
                    None  # TODO raise error when frontend starts treating it properly
                )
                # raise errors.FieldShouldBeLenghtier(field="q", min_length=3)
            if q.strip() == "":
                return None
        return q


@dataclasses.dataclass
class AnalyticalResult:  # pylint: disable=too-many-instance-attributes
    """
    Result data to analytical database.
    """

    school_uuid: uuid.UUID
    school_name: str
    school_city: str
    school_region: str | None
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
