from __future__ import annotations

import datetime
import uuid

from pydantic import BaseModel


class RegisterUploadItem(BaseModel):
    filename: str
    content_type: str
    size_bytes: int


class RegisterUploadsRequest(BaseModel):
    files: list[RegisterUploadItem]


class RegisterUploadItemResponse(BaseModel):
    id: uuid.UUID
    filename: str
    signed_url: str


class RegisterUploadsResponse(BaseModel):
    files: list[RegisterUploadItemResponse]


class KnowledgeBaseFileGet(BaseModel):
    id: uuid.UUID
    filename: str
    file_path: str
    bucket_name: str
    content_type: str
    size_bytes: int
    status: str
    transcription: str | None = None
    description: str | None = None
    indexing_status: str
    vector_status: str
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        orm_mode = True
        from_attributes = True


class ConfirmUploadResponse(BaseModel):
    id: uuid.UUID
    status: str
    message: str
