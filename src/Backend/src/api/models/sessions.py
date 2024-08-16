"""
Module used to build User structure.
"""

from __future__ import annotations

import datetime
import uuid

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as psql
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api import db

from . import users


class Session(db.Base):
    """
    Session model.
    """

    __tablename__ = "sessions"
    id: Mapped[db.UuidPk]

    user_id: Mapped[uuid.UUID] = mapped_column(
        psql.UUID(as_uuid=True),
        sa.ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )

    expires_at: Mapped[datetime.datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
    )

    generation: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)

    created_at: Mapped[db.DateTime] = mapped_column(
        init=False, default=datetime.datetime.now(tz=datetime.UTC)
    )

    updated_at: Mapped[db.DateTime] = mapped_column(
        init=False, default=datetime.datetime.now(tz=datetime.UTC)
    )

    user: Mapped[users.User] = relationship(
        "User",
        init=False,
        lazy="joined",
    )
