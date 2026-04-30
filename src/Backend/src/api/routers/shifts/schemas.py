import datetime
import uuid
import pydantic

class ShiftBase(pydantic.BaseModel):
    name: str
    code: str

class ShiftCreate(ShiftBase):
    pass

class ShiftGet(ShiftBase):
    id: uuid.UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        orm_mode = True

class ShiftList(pydantic.BaseModel):
    items: list[ShiftGet]
    pages: int
    current_page: int
    total: int
