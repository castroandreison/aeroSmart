from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import date

from app.core.database import get_session
from app.core.security import get_current_user
from app.models.usuario import Usuario, NivelAcesso
from app.schemas.financeiro import FinanceiroResponse, FinanceiroResumo
from app.services.financeiro_service import FinanceiroService
from app.services.agendamento_service import AgendamentoService
from app.models.financeiro import Financeiro
from app.models.agendamento import Agendamento
from sqlalchemy import select

router = APIRouter(prefix="/financeiro", tags=["Financeiro"])


@router.get("/", response_model=List[FinanceiroResponse])
async def listar_financeiro(
    session: AsyncSession = Depends(get_session),
    current_user: Usuario = Depends(get_current_user),
):
    if current_user.nivel_acesso == NivelAcesso.PROPRIETARIO:
        result = await session.execute(select(Financeiro).order_by(Financeiro.created_at.desc()))
        return list(result.scalars().all())
    if current_user.nivel_acesso == NivelAcesso.ADMINISTRADOR:
        query = select(Financeiro).join(Agendamento).join(Usuario, Usuario.id == Agendamento.usuario_id)
        if current_user.aeroclube_id:
            query = query.where(Usuario.aeroclube_id == current_user.aeroclube_id)
        result = await session.execute(query.order_by(Financeiro.created_at.desc()))
        return list(result.scalars().all())
    result = await session.execute(
        select(Financeiro)
        .join(Agendamento)
        .where(Agendamento.usuario_id == current_user.id)
        .order_by(Financeiro.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/resumo", response_model=FinanceiroResumo)
async def resumo_financeiro(
    data_inicio: str,
    data_fim: str,
    session: AsyncSession = Depends(get_session),
    current_user: Usuario = Depends(get_current_user),
):
    service = FinanceiroService(session)
    dt_inicio = date.fromisoformat(data_inicio)
    dt_fim = date.fromisoformat(data_fim)
    return await service.resumo_periodo(dt_inicio, dt_fim)


@router.get("/calcular-custos")
async def calcular_custos(
    tempo_minutos: float,
    session: AsyncSession = Depends(get_session),
    current_user: Usuario = Depends(get_current_user),
):
    service = FinanceiroService(session)
    return await service.calcular_custos(tempo_minutos, aeroclube_id=current_user.aeroclube_id)
