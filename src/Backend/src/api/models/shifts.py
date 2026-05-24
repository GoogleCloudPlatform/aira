import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from api import db


class WorkShift(db.Base, db.DefaultColumns):
    """
    WorkShift model.
    """

    __tablename__ = "work_shifts"

    name: Mapped[str] = mapped_column(sa.String(50), unique=True, nullable=False)
    code: Mapped[str] = mapped_column(sa.String(20), unique=True, nullable=False)

    def __repr__(self) -> str:
        return f"WorkShift(id={self.id}, name={self.name})"
