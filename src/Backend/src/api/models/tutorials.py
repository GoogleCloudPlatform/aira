import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from api import db


class Tutorial(db.Base, db.DefaultColumns):
    """
    Tutorial model to store tutorial files and references for different audiences.
    """

    __tablename__ = "tutorials"

    audience: Mapped[db.Str50] = mapped_column(nullable=False)  # 'educator' or 'admin'
    source_type: Mapped[db.Str50] = mapped_column(nullable=False)  # 'upload' or 'link'
    filename: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    file_path: Mapped[str | None] = mapped_column(sa.String(512), nullable=True)
    bucket_name: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    url: Mapped[str] = mapped_column(sa.String(1024), nullable=False)

    def __repr__(self) -> str:
        return (
            f"Tutorial(id={self.id}, audience={self.audience}, "
            f"source_type={self.source_type}, url={self.url})"
        )
