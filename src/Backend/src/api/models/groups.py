"""
Module for the groups model, aka classes.
"""

import enum

import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.dialects import postgresql as psql
from sqlalchemy.orm import Mapped, mapped_column

from api import db

from . import organizations


class Grades(enum.StrEnum):
    """
    Available grades.
    """

    FIRST_FUND = "1º Ano"
    SECOND_FUND = "2º Ano"
    THIRD_FUND = "3º Ano"
    FOURTH_FUND = "4º Ano"
    FIFTH_FUND = "5º Ano"
    SIXTH_FUND = "6º Ano"
    SEVENTH_FUND = "7º Ano"
    EIGHTH_FUND = "8º Ano"
    NINETH_FUND = "9º Ano"
    FIRST_HS = "1ª Série"
    SECOND_HS = "2ª Série"
    THIRD_HS = "3ª Série"


class Shifts(enum.StrEnum):
    """
    Available shifts.
    """

    MORNING = "morning"
    AFTERNOON = "afternoon"
    EVENING = "evening"
    ALLDAY = "allday"


class Group(db.Base, db.DefaultColumns):
    """
    Group model.
    """

    __tablename__ = "groups"

    name: Mapped[db.Str50]

    customer_id: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)

    organization_id: Mapped[db.UuidDefault] = mapped_column(
        sa.ForeignKey("organizations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    grade: Mapped[Grades] = mapped_column(psql.ENUM(Grades), nullable=False)
    shift: Mapped[Shifts] = mapped_column(psql.ENUM(Shifts), nullable=False)

    organization: Mapped[organizations.Organization] = orm.relationship(
        organizations.Organization,
        init=False,
    )

    def __repr__(self) -> str:
        return f"Group(id={self.id}, name={self.name})"
