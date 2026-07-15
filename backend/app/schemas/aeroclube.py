from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AeroclubeCreate(BaseModel):
    nome: str


class AeroclubeUpdate(BaseModel):
    nome: Optional[str] = None


class AeroclubeResponse(BaseModel):
    id: int
    nome: str
    topic_write: Optional[str] = None
    topic_read: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
