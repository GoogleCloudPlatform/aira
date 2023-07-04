"""
Module for the organizations model, aka schools.
"""
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from api import db


class Organization(db.Base, db.DefaultColumns):
    """
    Organization model.
    """

    __tablename__ = "organizations"

    customer_id: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)

    name: Mapped[db.Str50]

    region: Mapped[str | None] = mapped_column(sa.String(50), nullable=True)
    city: Mapped[db.Str50]
    state: Mapped[str] = mapped_column(sa.String(2))
