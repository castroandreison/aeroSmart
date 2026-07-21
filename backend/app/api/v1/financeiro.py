from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import date, datetime

from app.core.database import get_session
from app.core.security import get_current_user
from app.models.usuario import Usuario, NivelAcesso
from app.schemas.financeiro import FinanceiroResponse, FinanceiroResumo
from app.services.financeiro_service import FinanceiroService
from app.services.agendamento_service import AgendamentoService
from app.models.financeiro import Financeiro
from app.models.agendamento import Agendamento
from app.models.acionamento import Acionamento
from app.core.timezone import SAO_PAULO_TZ
from sqlalchemy import select, delete, func
from sqlalchemy.orm import selectinload

router = APIRouter(prefix="/financeiro", tags=["Financeiro"])


def _build_financeiro_response(f: Financeiro) -> FinanceiroResponse:
    ag = f.agendamento
    duracao = None
    if ag and ag.hora_inicio and ag.hora_termino:
        duracao = round((ag.hora_termino - ag.hora_inicio).total_seconds() / 60, 1)
    return FinanceiroResponse(
        id=f.id,
        agendamento_id=f.agendamento_id,
        tempo_ligado_minutos=f.tempo_ligado_minutos,
        data=ag.data if ag else None,
        hora_inicio=ag.hora_inicio if ag else None,
        hora_termino=ag.hora_termino if ag else None,
        duracao_minutos=duracao,
        energia_consumida_kwh=f.energia_consumida_kwh,
        valor_energia=f.valor_energia,
        valor_acionamento=f.valor_acionamento,
        impostos=f.impostos,
        taxas_extras=f.taxas_extras,
        valor_total=f.valor_total,
        pago=f.pago,
    )


@router.get("/", response_model=List[FinanceiroResponse])
async def listar_financeiro(
    session: AsyncSession = Depends(get_session),
    current_user: Usuario = Depends(get_current_user),
):
    query = select(Financeiro).options(selectinload(Financeiro.agendamento)).order_by(Financeiro.created_at.desc())

    if current_user.nivel_acesso == NivelAcesso.PROPRIETARIO:
        pass
    elif current_user.nivel_acesso == NivelAcesso.ADMINISTRADOR:
        query = query.join(Agendamento).join(Usuario, Usuario.id == Agendamento.usuario_id)
        if current_user.aeroclube_id:
            query = query.where(Usuario.aeroclube_id == current_user.aeroclube_id)
    else:
        query = query.join(Agendamento).where(Agendamento.usuario_id == current_user.id)

    result = await session.execute(query)
    return [_build_financeiro_response(f) for f in result.scalars().all()]


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


@router.delete("/dados")
async def apagar_dados_teste(
    session: AsyncSession = Depends(get_session),
    current_user: Usuario = Depends(get_current_user),
):
    if current_user.nivel_acesso not in (NivelAcesso.PROPRIETARIO, NivelAcesso.ADMINISTRADOR):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")

    qtd_financeiro = (await session.execute(select(func.count(Financeiro.id)))).scalar()
    qtd_acionamento = (await session.execute(select(func.count(Acionamento.id)))).scalar()
    qtd_agendamentos = (await session.execute(select(func.count(Agendamento.id)))).scalar()

    await session.execute(delete(Financeiro))
    await session.execute(delete(Acionamento))
    await session.execute(delete(Agendamento))
    await session.commit()

    return {
        "message": "Todos os dados apagados com sucesso",
        "financeiro": qtd_financeiro,
        "acionamentos": qtd_acionamento,
        "agendamentos": qtd_agendamentos,
    }
