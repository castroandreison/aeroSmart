from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime


class LogResponse(BaseModel):
    id: int
    usuario_id: Optional[int] = None
    usuario_nome: Optional[str] = None
    acao: str
    entidade: Optional[str] = None
    entidade_id: Optional[int] = None
    descricao: Optional[str] = None
    detalhes: Optional[Any] = None
    ip: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
