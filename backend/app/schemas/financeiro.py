from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class FinanceiroResponse(BaseModel):
    id: int
    agendamento_id: int
    tempo_ligado_minutos: Optional[float] = None
    energia_consumida_kwh: Optional[float] = None
    valor_energia: Optional[float] = None
    valor_acionamento: Optional[float] = None
    impostos: Optional[float] = None
    taxas_extras: Optional[float] = None
    valor_total: Optional[float] = None
    pago: bool

    class Config:
        from_attributes = True


class FinanceiroResumo(BaseModel):
    total_receita: float
    total_custos: float
    total_energia_kwh: float
    total_horas: float
    total_acionamentos: int
    periodo_inicio: Optional[datetime] = None
    periodo_fim: Optional[datetime] = None
