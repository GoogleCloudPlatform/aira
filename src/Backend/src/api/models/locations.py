"""
Module for location models (Country, State, City).
"""

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api import db


class Country(db.Base, db.DefaultColumns):
    """
    Country model.
    """

    __tablename__ = "countries"

    name: Mapped[db.Str100] = mapped_column(unique=True)
    code: Mapped[str] = mapped_column(sa.String(5), unique=True)
    is_default: Mapped[bool] = mapped_column(default=False)

    states: Mapped[list["State"]] = relationship("State", back_populates="country", init=False)


class State(db.Base, db.DefaultColumns):
    """
    State model.
    """

    __tablename__ = "states"

    name: Mapped[db.Str100]
    code: Mapped[str] = mapped_column(sa.String(5))
    country_id: Mapped[db.UuidDefault] = mapped_column(
        sa.ForeignKey("countries.id", ondelete="CASCADE"),
        nullable=False,
    )

    country: Mapped["Country"] = relationship("Country", back_populates="states", init=False)
    cities: Mapped[list["City"]] = relationship("City", back_populates="state", init=False)

    __table_args__ = (
        sa.UniqueConstraint("name", "country_id", name="uix_state_name_country"),
        sa.UniqueConstraint("code", "country_id", name="uix_state_code_country"),
    )


class City(db.Base, db.DefaultColumns):
    """
    City model.
    """

    __tablename__ = "cities"

    name: Mapped[db.Str100]
    state_id: Mapped[db.UuidDefault] = mapped_column(
        sa.ForeignKey("states.id", ondelete="CASCADE"),
        nullable=False,
    )

    state: Mapped["State"] = relationship("State", back_populates="cities", init=False)

    __table_args__ = (
        sa.UniqueConstraint("name", "state_id", name="uix_city_name_state"),
    )
