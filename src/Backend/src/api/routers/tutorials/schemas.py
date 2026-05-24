from __future__ import annotations

import datetime
import uuid

from pydantic import BaseModel


class TutorialGet(BaseModel):
    id: uuid.UUID
    audience: str
    source_type: str
    filename: str | None = None
    file_path: str | None = None
    bucket_name: str | None = None
    url: str
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        orm_mode = True
        from_attributes = True  # in Pydantic v2, this is equivalent to orm_mode
