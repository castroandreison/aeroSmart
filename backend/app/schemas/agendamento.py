from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AgendamentoCreate(BaseModel):
    data: str
    hora_inicio: str
    hora_termino: str
    aeronave_id: int
    aeroclube_id: int
    observacoes: Optional[str] = None


class AgendamentoUpdate(BaseModel):
    data: Optional[str] = None
    hora_inicio: Optional[str] = None
    hora_termino: Optional[str] = None
    aeronave_id: Optional[int] = None
    aeroclube_id: Optional[int] = None
    observacoes: Optional[str] = None


class AgendamentoResponse(BaseModel):
    id: int
    data: datetime
    hora_inicio: datetime
    hora_termino: datetime
    observacoes: Optional[str] = None
    status: str
    usuario_id: int
    aeronave_id: int
    aeroclube_id: Optional[int] = None
    aeroclube_nome: Optional[str] = None
    solicitante_nome: Optional[str] = None
    aeronave_matricula: Optional[str] = None
    aeronave_modelo: Optional[str] = None
    tempo_balizamento_minutos: Optional[float] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AgendamentoDetail(AgendamentoResponse):
    data_cadastro: Optional[datetime] = None
    hora_cadastro: Optional[datetime] = None
    usuario_responsavel: Optional[str] = None
