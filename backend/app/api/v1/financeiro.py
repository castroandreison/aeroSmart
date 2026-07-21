from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import date, datetime, timedelta

from app.core.database import get_session
from app.core.security import get_current_user
from app.models.usuario import Usuario, NivelAcesso
from app.schemas.financeiro import FinanceiroResponse, FinanceiroResumo
from app.services.financeiro_service import FinanceiroService
from app.services.agendamento_service import AgendamentoService
from app.models.financeiro import Financeiro
from app.models.agendamento import Agendamento, StatusAgendamento
from app.models.acionamento import Acionamento
from app.models.aeronave import Aeronave
from app.core.timezone import SAO_PAULO_TZ
from sqlalchemy import select, delete, func

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


@router.post("/gerar-dados-teste")
async def gerar_dados_teste(
    session: AsyncSession = Depends(get_session),
    current_user: Usuario = Depends(get_current_user),
):
    if current_user.nivel_acesso not in (NivelAcesso.PROPRIETARIO, NivelAcesso.ADMINISTRADOR):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")

    aeroclube_id = current_user.aeroclube_id or 5

    result = await session.execute(select(Usuario).where(Usuario.nivel_acesso == NivelAcesso.SOLICITANTE, Usuario.aeroclube_id == aeroclube_id).limit(2))
    solicitantes = list(result.scalars().all())
    if not solicitantes:
        raise HTTPException(status_code=400, detail="Nenhum solicitante encontrado no aeroclube")

    result = await session.execute(
        select(Aeronave)
        .join(Usuario, Aeronave.usuario_id == Usuario.id)
        .where(Usuario.aeroclube_id == aeroclube_id)
        .limit(2)
    )
    aeronaves = list(result.scalars().all())
    if not aeronaves:
        aeronaves = list((await session.execute(select(Aeronave).limit(2))).scalars().all())
    if not aeronaves:
        raise HTTPException(status_code=400, detail="Nenhuma aeronave encontrada")

    agora = datetime.now(SAO_PAULO_TZ)
    financeiro_service = FinanceiroService(session)
    criados = {"agendamentos_futuros": 0, "agendamentos_passados": 0}

    for i, dias in enumerate([-3, -1]):
        data_hora = agora + timedelta(days=dias, hours=8)
        termino = data_hora + timedelta(hours=1)
        if dias < 0 and data_hora < agora and termino < agora:
            status_ag = StatusAgendamento.CONCLUIDO
        else:
            status_ag = StatusAgendamento.AGENDADO

        ag = Agendamento(
            data=data_hora,
            hora_inicio=data_hora,
            hora_termino=termino,
            usuario_id=solicitantes[i % len(solicitantes)].id,
            aeronave_id=aeronaves[i % len(aeronaves)].id,
            aeroclube_id=aeroclube_id,
            status=status_ag,
            observacoes=f"Teste {dias} dias",
        )
        session.add(ag)
        await session.commit()
        await session.refresh(ag)

        if status_ag == StatusAgendamento.CONCLUIDO:
            tempo_seg = 3000 + i * 600
            acionamento = Acionamento(
                agendamento_id=ag.id,
                data_hora_ligamento=data_hora,
                data_hora_desligamento=termino,
                tempo_ligado_segundos=tempo_seg,
                status="concluido",
                confirmado=True,
            )
            session.add(acionamento)
            await session.commit()

            custos = await financeiro_service.calcular_custos(tempo_seg / 60, aeroclube_id=aeroclube_id)
            financeiro_rec = Financeiro(
                agendamento_id=ag.id,
                **custos,
            )
            session.add(financeiro_rec)
            await session.commit()
            criados["agendamentos_passados"] += 1
        else:
            criados["agendamentos_futuros"] += 1

    for i, dias in enumerate([1, 2]):
        data_hora = agora + timedelta(days=dias, hours=10)
        termino = data_hora + timedelta(hours=1, minutes=30)

        ag = Agendamento(
            data=data_hora,
            hora_inicio=data_hora,
            hora_termino=termino,
            usuario_id=solicitantes[i % len(solicitantes)].id,
            aeronave_id=aeronaves[(i + 1) % len(aeronaves)].id,
            aeroclube_id=aeroclube_id,
            status=StatusAgendamento.AGENDADO,
            observacoes=f"Teste +{dias} dias",
        )
        session.add(ag)
        criados["agendamentos_futuros"] += 1

    await session.commit()

    return {
        "message": "Dados de teste criados com sucesso",
        "agendamentos_passados": criados["agendamentos_passados"],
        "agendamentos_futuros": criados["agendamentos_futuros"],
    }


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
