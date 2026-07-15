from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class StatusPista(BaseModel):
    status: str
    tempo_restante_segundos: Optional[float] = None
    tempo_ligado_segundos: Optional[float] = None
    horario_real_ligamento: Optional[datetime] = None
    proximo_agendamento: Optional[datetime] = None
    usuario_responsavel: Optional[str] = None
    ultimo_acionamento: Optional[datetime] = None
    controlador_online: bool = False
    camera_online: bool = False


class DashboardAdmin(BaseModel):
    agendamentos_dia: int = 0
    agendamentos_futuros: int = 0
    agendamentos_concluidos: int = 0
    usuarios_ativos: int = 0
    horas_utilizacao: float = 0
    consumo_energia: float = 0
    receita: float = 0
    custos: float = 0
    economia: float = 0
    numero_acionamentos: int = 0
    tempo_medio_ligado_min: float = 0


class DashboardSolicitante(BaseModel):
    proximo_voo: Optional[datetime] = None
    proximo_agendamento: Optional[str] = None
    total_horas: float = 0
    total_gasto: float = 0
    total_energia: float = 0
    total_voos: int = 0


class AeroclubeResumo(BaseModel):
    aeroclube_id: int
    aeroclube_nome: str
    total_voos: int = 0
    total_horas: float = 0
    total_energia_kwh: float = 0
    total_gasto: float = 0
    usuarios_ativos: int = 0


class DashboardProprietario(BaseModel):
    total_aeroclubes: int
    total_voos: int
    total_horas: float
    total_energia_kwh: float
    total_gasto: float
    total_usuarios_ativos: int
    aeroclubes: list[AeroclubeResumo]
