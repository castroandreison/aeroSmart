from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Optional
import json
import asyncio

from app.core.database import get_session
from app.core.security import get_current_user
from app.models.usuario import Usuario, NivelAcesso
from app.models.agendamento import Agendamento, StatusAgendamento
from app.models.acionamento import Acionamento
from app.models.aeroclube import Aeroclube
from app.models.financeiro import Financeiro
from app.schemas.monitoramento import StatusPista, DashboardAdmin, DashboardSolicitante, DashboardProprietario, AeroclubeResumo
from app.services.automacao_service import AutomacaoService
from app.services.camera_service import CameraService
from app.services.financeiro_service import FinanceiroService

router = APIRouter(prefix="/monitoramento", tags=["Monitoramento"])


@router.get("/status-pista", response_model=StatusPista)
async def get_status_pista(
    session: AsyncSession = Depends(get_session),
    current_user: Usuario = Depends(get_current_user),
):
    automacao = AutomacaoService(session)
    status = await automacao.get_status_pista()

    prox = None
    if status.get("proximo_agendamento"):
        prox = status["proximo_agendamento"]

    return StatusPista(
        status=status.get("status", "desligado"),
        tempo_restante_segundos=status.get("tempo_restante_segundos", 0),
        tempo_ligado_segundos=status.get("tempo_ligado_segundos", 0),
        proximo_agendamento=prox,
        usuario_responsavel=None,
        controlador_online=True,
        camera_online=False,
    )


@router.get("/dashboard-admin", response_model=DashboardAdmin)
async def dashboard_admin(
    session: AsyncSession = Depends(get_session),
    current_user: Usuario = Depends(get_current_user),
):
    if current_user.nivel_acesso not in (NivelAcesso.PROPRIETARIO, NivelAcesso.ADMINISTRADOR):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso restrito")

    from sqlalchemy import cast, Date
    today = func.current_date()

    def _apply_ac_filter(query):
        if current_user.nivel_acesso == NivelAcesso.ADMINISTRADOR and current_user.aeroclube_id:
            return query.join(Usuario, Usuario.id == Agendamento.usuario_id).where(Usuario.aeroclube_id == current_user.aeroclube_id)
        return query

    agendamentos_dia = await session.execute(
        _apply_ac_filter(select(func.count(Agendamento.id)).where(cast(Agendamento.data, Date) == today))
    )
    agendamentos_futuros = await session.execute(
        _apply_ac_filter(select(func.count(Agendamento.id)).where(
            Agendamento.status == StatusAgendamento.AGENDADO,
            Agendamento.hora_inicio > func.now(),
        ))
    )
    agendamentos_concluidos = await session.execute(
        _apply_ac_filter(select(func.count(Agendamento.id)).where(Agendamento.status == StatusAgendamento.CONCLUIDO))
    )

    financeiro = FinanceiroService(session)
    from datetime import datetime, timedelta
    inicio_mes = datetime.now().replace(day=1).date()
    fim_mes = datetime.now().date()
    aeroclube_nome = current_user.aeroclube if current_user.nivel_acesso == NivelAcesso.ADMINISTRADOR else None
    resumo = await financeiro.resumo_periodo(inicio_mes, fim_mes, aeroclube=aeroclube_nome)

    return DashboardAdmin(
        agendamentos_dia=agendamentos_dia.scalar() or 0,
        agendamentos_futuros=agendamentos_futuros.scalar() or 0,
        agendamentos_concluidos=agendamentos_concluidos.scalar() or 0,
        usuarios_ativos=0,
        horas_utilizacao=resumo["total_horas"],
        consumo_energia=resumo["total_energia_kwh"],
        receita=resumo["total_gasto"],
        numero_acionamentos=resumo["total_voos"],
    )


@router.get("/dashboard-solicitante", response_model=DashboardSolicitante)
async def dashboard_solicitante(
    session: AsyncSession = Depends(get_session),
    current_user: Usuario = Depends(get_current_user),
):
    result = await session.execute(
        select(Agendamento)
        .where(
            Agendamento.usuario_id == current_user.id,
            Agendamento.status == StatusAgendamento.AGENDADO,
            Agendamento.hora_inicio > func.now(),
        )
        .order_by(Agendamento.hora_inicio)
        .limit(1)
    )
    proximo = result.scalar_one_or_none()

    financeiro = FinanceiroService(session)
    result_total = await session.execute(
        select(
            func.count(Agendamento.id),
            func.sum(Acionamento.tempo_ligado_segundos),
        )
        .outerjoin(Acionamento, Acionamento.agendamento_id == Agendamento.id)
        .where(
            Agendamento.usuario_id == current_user.id,
            Agendamento.status == StatusAgendamento.CONCLUIDO,
        )
    )
    row = result_total.one()
    total_voos = row[0] or 0
    total_segundos = row[1] or 0

    return DashboardSolicitante(
        proximo_voo=proximo.hora_inicio if proximo else None,
        proximo_agendamento=proximo.hora_inicio.strftime("%d/%m/%Y %H:%M") if proximo else None,
        total_horas=round((total_segundos or 0) / 3600, 2),
        total_voos=total_voos,
    )


@router.get("/dashboard-proprietario", response_model=DashboardProprietario)
async def dashboard_proprietario(
    session: AsyncSession = Depends(get_session),
    current_user: Usuario = Depends(get_current_user),
):
    if current_user.nivel_acesso != NivelAcesso.PROPRIETARIO:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso restrito ao proprietário")

    query = select(
        Aeroclube.id,
        Aeroclube.nome,
        func.count(Financeiro.id).label("total_voos"),
        func.coalesce(func.sum(Financeiro.tempo_ligado_minutos), 0).label("total_minutos"),
        func.coalesce(func.sum(Financeiro.energia_consumida_kwh), 0).label("total_energia"),
        func.coalesce(func.sum(Financeiro.valor_total), 0).label("total_gasto"),
        func.count(func.distinct(Usuario.id)).filter(Usuario.ativo == True).label("usuarios_ativos"),
    ).outerjoin(Usuario, Usuario.aeroclube_id == Aeroclube.id) \
     .outerjoin(Agendamento, and_(Agendamento.usuario_id == Usuario.id, Agendamento.status == StatusAgendamento.CONCLUIDO)) \
     .outerjoin(Financeiro, Financeiro.agendamento_id == Agendamento.id) \
     .group_by(Aeroclube.id, Aeroclube.nome) \
     .order_by(Aeroclube.nome)

    result = await session.execute(query)
    rows = result.all()

    aeroclubes = []
    tot_voos = tot_horas = tot_energia = tot_gasto = tot_usuarios = 0
    for r in rows:
        horas = round((r.total_minutos or 0) / 60, 2)
        aeroclubes.append(AeroclubeResumo(
            aeroclube_id=r.id,
            aeroclube_nome=r.nome,
            total_voos=r.total_voos or 0,
            total_horas=horas,
            total_energia_kwh=round(float(r.total_energia or 0), 2),
            total_gasto=round(float(r.total_gasto or 0), 2),
            usuarios_ativos=r.usuarios_ativos or 0,
        ))
        tot_voos += r.total_voos or 0
        tot_horas += horas
        tot_energia += float(r.total_energia or 0)
        tot_gasto += float(r.total_gasto or 0)
        tot_usuarios += r.usuarios_ativos or 0

    return DashboardProprietario(
        total_aeroclubes=len(aeroclubes),
        total_voos=tot_voos,
        total_horas=round(tot_horas, 2),
        total_energia_kwh=round(tot_energia, 2),
        total_gasto=round(tot_gasto, 2),
        total_usuarios_ativos=tot_usuarios,
        aeroclubes=aeroclubes,
    )


@router.get("/camera/snapshot")
async def camera_snapshot(
    current_user: Usuario = Depends(get_current_user),
):
    camera = CameraService()
    snapshot = await camera.obter_snapshot_base64()
    if not snapshot:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Câmera indisponível")
    return {"snapshot": snapshot, "formato": "image/jpeg"}


@router.get("/camera/status")
async def camera_status(
    current_user: Usuario = Depends(get_current_user),
):
    camera = CameraService()
    online = await camera.verificar_online()
    return {"online": online}


@router.get("/stream")
async def stream_status(
    session: AsyncSession = Depends(get_session),
    current_user: Usuario = Depends(get_current_user),
):
    async def event_generator():
        while True:
            try:
                automacao = AutomacaoService(session)
                status = await automacao.get_status_pista()
                yield f"data: {json.dumps(status)}\n\n"
                await asyncio.sleep(2)
            except asyncio.CancelledError:
                break
            except Exception:
                yield f"data: {json.dumps({'status': 'erro'})}\n\n"
                await asyncio.sleep(5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
