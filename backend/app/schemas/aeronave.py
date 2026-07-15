from pydantic import BaseModel
from typing import Optional


class AeronaveCreate(BaseModel):
    matricula: str
    modelo: str
    fabricante: Optional[str] = None
    tipo: Optional[str] = None
    peso_maximo: Optional[float] = None
    operador: Optional[str] = None


class AeronaveUpdate(BaseModel):
    matricula: Optional[str] = None
    modelo: Optional[str] = None
    fabricante: Optional[str] = None
    tipo: Optional[str] = None
    peso_maximo: Optional[float] = None
    operador: Optional[str] = None


class AeronaveResponse(BaseModel):
    id: int
    matricula: str
    modelo: str
    fabricante: Optional[str] = None
    tipo: Optional[str] = None
    peso_maximo: Optional[float] = None
    operador: Optional[str] = None
    usuario_id: int
    usuario_nome: Optional[str] = None
    aeroclube: Optional[str] = None
    aeroclube_id: Optional[int] = None

    class Config:
        from_attributes = True
