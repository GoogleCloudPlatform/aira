import datetime
import uuid

from pydantic import BaseModel


class SeriesBase(BaseModel):
    name: str
    code: str


class SeriesCreate(SeriesBase):
    pass


class SeriesGet(SeriesBase):
    id: uuid.UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        orm_mode = True
