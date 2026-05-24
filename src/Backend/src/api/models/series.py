import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from api import db


class Series(db.Base, db.DefaultColumns):
    """
    Series model.
    """

    __tablename__ = "series"

    name: Mapped[str] = mapped_column(sa.String(50), unique=True, nullable=False)
    code: Mapped[str] = mapped_column(sa.String(10), unique=True, nullable=False)

    def __repr__(self) -> str:
        return f"Series(id={self.id}, name={self.name})"
