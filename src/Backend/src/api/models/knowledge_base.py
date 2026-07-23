import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from api import db


class KnowledgeBaseFile(db.Base, db.DefaultColumns):
    """
    Model representing a file in the pedagogical knowledge base.
    """

    __tablename__ = "knowledge_base_files"

    # Non-default fields first
    filename: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(sa.String(512), nullable=False)
    content_type: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(sa.BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(sa.String(50), nullable=False)

    # Default fields next
    bucket_name: Mapped[str] = mapped_column(
        sa.String(255), nullable=False, default="aira-kb-files"
    )
    transcription: Mapped[str | None] = mapped_column(
        sa.Text, nullable=True, default=None
    )
    description: Mapped[str | None] = mapped_column(
        sa.Text, nullable=True, default=None
    )
    indexing_status: Mapped[str] = mapped_column(
        sa.String(50), nullable=False, default="pending"
    )
    vector_status: Mapped[str] = mapped_column(
        sa.String(50), nullable=False, default="pending"
    )

    def __repr__(self) -> str:
        return (
            f"KnowledgeBaseFile(id={self.id}, filename={self.filename}, "
            f"content_type={self.content_type}, status={self.status})"
        )
