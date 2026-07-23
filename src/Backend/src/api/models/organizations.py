"""
Module for the organizations model, aka schools.
"""

import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api import db


class Organization(db.Base, db.DefaultColumns):
    """
    Organization model.
    """

    __tablename__ = "organizations"

    name: Mapped[db.Str50]
    city: Mapped[db.Str50]
    state: Mapped[str] = mapped_column(sa.String(2))

    customer_id: Mapped[str | None] = mapped_column(sa.String(100), nullable=True, default=None)
    region: Mapped[str | None] = mapped_column(sa.String(50), nullable=True, default=None)
    city_id: Mapped[db.UuidDefault | None] = mapped_column(
        sa.ForeignKey("cities.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )
    city_rel: Mapped["City"] = relationship("City", init=False)

    @property
    def country_id(self) -> uuid.UUID | None:
        return (
            self.city_rel.state.country_id
            if self.city_rel and self.city_rel.state
            else None
        )

    @property
    def state_id(self) -> uuid.UUID | None:
        return self.city_rel.state_id if self.city_rel else None
