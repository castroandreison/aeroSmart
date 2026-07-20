from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from typing import List, Optional
from datetime import date

from app.core.database import get_session
from app.core.security import get_current_user
from app.models.usuario import Usuario, NivelAcesso
from app.models.agendamento import Agendamento
from app.models.aeroclube import Aeroclube
from app.schemas.agendamento import AgendamentoCreate, AgendamentoUpdate, AgendamentoResponse
from app.services.agendamento_service import AgendamentoService
from app.services.usuario_service import UsuarioService
from app.services.mqtt_service import mqtt_service

router = APIRouter(prefix="/agendamentos", tags=["Agendamentos"])


async def _aeroclube_do_ag(ag: Agendamento, session: AsyncSession = None) -> tuple:
    """Extrai (id, nome) do aeroclube do agendamento.
    Tenta relacao carregada primeiro; se nao encontrada, busca no banco."""
    if ag and ag.aeroclube_rel:
        return ag.aeroclube_rel.id, ag.aeroclube_rel.nome
    if ag and ag.aeroclube_id and session:
        result = await session.execute(
            select(Aeroclube).where(Aeroclube.id == ag.aeroclube_id)
        )
        aero = result.scalar_one_or_none()
        if aero:
            return aero.id, aero.nome
    return None, None


async def _publicar_agendamento_mqtt(ag: Agendamento, session: AsyncSession = None):
    """Envia dados do agendamento para a estacao via MQTT"""
    aero_id, aero_nome = await _aeroclube_do_ag(ag, session)
    if not aero_id or not aero_nome:
        print(f"[agendamentos] Agendamento {ag.id}: aeroclube nao encontrado, pulando MQTT")
        return
    duracao_segundos = int((ag.hora_termino - ag.hora_inicio).total_seconds())
    ag_data = {
        "id": ag.id,
        "data": ag.hora_inicio.strftime("%d/%m/%Y"),
        "hora_inicio": ag.hora_inicio.strftime("%H:%M:%S"),
        "hora_fim": ag.hora_termino.strftime("%H:%M:%S"),
        "duracao_segundos": duracao_segundos,
    }
    print(f"[agendamentos] Publicando agendamento {ag.id} via MQTT para {aero_nome}: {ag_data}")
    try:
        ok = await mqtt_service.enviar_agendamento(aero_id, aero_nome, ag_data)
        print(f"[agendamentos] MQTT publicacao agendamento {ag.id}: {'OK' if ok else 'FALHA'}")
    except Exception as e:
        print(f"[agendamentos] Erro ao publicar agendamento {ag.id} via MQTT: {e}")


async def _cancelar_agendamento_mqtt(ag: Agendamento, session: AsyncSession = None):
    """Envia cancelamento do agendamento para a estacao via MQTT"""
    aero_id, aero_nome = await _aeroclube_do_ag(ag, session)
    if not aero_id or not aero_nome:
        return
    print(f"[agendamentos] Cancelando agendamento {ag.id} via MQTT para {aero_nome}")
    try:
        await mqtt_service.enviar_cancelamento_agendamento(aero_id, aero_nome, ag.id)
    except Exception as e:
        print(f"[agendamentos] Erro ao cancelar agendamento {ag.id} via MQTT: {e}")


@router.get("/", response_model=List[AgendamentoResponse])
async def listar_agendamentos(
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    status: Optional[str] = None,
    incluir_finalizados: bool = False,
    session: AsyncSession = Depends(get_session),
    current_user: Usuario = Depends(get_current_user),
):
    service = AgendamentoService(session)
    dt_inicio = date.fromisoformat(data_inicio) if data_inicio else None
    dt_fim = date.fromisoformat(data_fim) if data_fim else None

    if current_user.nivel_acesso == NivelAcesso.PROPRIETARIO:
        agendamentos = await service.listar(data_inicio=dt_inicio, data_fim=dt_fim, status=status, incluir_finalizados=incluir_finalizados)
    elif current_user.nivel_acesso == NivelAcesso.ADMINISTRADOR:
        agendamentos = await service.listar(data_inicio=dt_inicio, data_fim=dt_fim, status=status, aeroclube_id=current_user.aeroclube_id, incluir_finalizados=incluir_finalizados)
    else:
        agendamentos = await service.listar(usuario_id=current_user.id, data_inicio=dt_inicio, data_fim=dt_fim, status=status, incluir_finalizados=incluir_finalizados)

    result = []
    for a in agendamentos:
        dif = (a.hora_termino - a.hora_inicio).total_seconds() / 60 if a.hora_inicio and a.hora_termino else None
        response = AgendamentoResponse(
            id=a.id,
            data=a.data,
            hora_inicio=a.hora_inicio,
            hora_termino=a.hora_termino,
            observacoes=a.observacoes,
            status=a.status.value if hasattr(a.status, 'value') else a.status,
            usuario_id=a.usuario_id,
            aeronave_id=a.aeronave_id,
            aeroclube_id=a.aeroclube_id,
            aeroclube_nome=a.aeroclube_rel.nome if a.aeroclube_rel else None,
            solicitante_nome=a.solicitante.nome_completo if a.solicitante else None,
            aeronave_matricula=a.aeronave.matricula if a.aeronave else None,
            aeronave_modelo=a.aeronave.modelo if a.aeronave else None,
            tempo_balizamento_minutos=round(dif, 1) if dif else None,
            created_at=a.created_at,
        )
        result.append(response)
    return result


@router.get("/{agendamento_id}", response_model=AgendamentoResponse)
async def obter_agendamento(
    agendamento_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: Usuario = Depends(get_current_user),
):
    service = AgendamentoService(session)
    agendamento = await service.obter_por_id(agendamento_id)
    if not agendamento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agendamento não encontrado")
    if current_user.nivel_acesso != NivelAcesso.ADMINISTRADOR and agendamento.usuario_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")
    dif = (agendamento.hora_termino - agendamento.hora_inicio).total_seconds() / 60 if agendamento.hora_inicio and agendamento.hora_termino else None
    return AgendamentoResponse(
        id=agendamento.id,
        data=agendamento.data,
        hora_inicio=agendamento.hora_inicio,
        hora_termino=agendamento.hora_termino,
        observacoes=agendamento.observacoes,
        status=agendamento.status.value if hasattr(agendamento.status, 'value') else agendamento.status,
        usuario_id=agendamento.usuario_id,
        aeronave_id=agendamento.aeronave_id,
        aeroclube_id=agendamento.aeroclube_id,
        aeroclube_nome=agendamento.aeroclube_rel.nome if agendamento.aeroclube_rel else None,
        solicitante_nome=agendamento.solicitante.nome_completo if agendamento.solicitante else None,
        aeronave_matricula=agendamento.aeronave.matricula if agendamento.aeronave else None,
        aeronave_modelo=agendamento.aeronave.modelo if agendamento.aeronave else None,
        tempo_balizamento_minutos=round(dif, 1) if dif else None,
        created_at=agendamento.created_at,
    )


@router.post("/", response_model=AgendamentoResponse, status_code=status.HTTP_201_CREATED)
async def criar_agendamento(
    data: AgendamentoCreate,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: Usuario = Depends(get_current_user),
):
    if current_user.nivel_acesso == NivelAcesso.ADMINISTRADOR and data.aeroclube_id != current_user.aeroclube_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrador só pode agendar no seu próprio aeroclube")
    service = AgendamentoService(session)
    try:
        agendamento = await service.criar(data, current_user.id)
        usuario_service = UsuarioService(session)
        await usuario_service.registrar_log(
            usuario_id=current_user.id,
            usuario_nome=current_user.nome_completo,
            acao="criar_agendamento",
            entidade="agendamento",
            entidade_id=agendamento.id,
            ip=request.client.host if request.client else None,
        )
        dif = (agendamento.hora_termino - agendamento.hora_inicio).total_seconds() / 60 if agendamento.hora_inicio and agendamento.hora_termino else None

        # Publica agendamento via MQTT para a estacao
        await _publicar_agendamento_mqtt(agendamento, session)

        return AgendamentoResponse(
            id=agendamento.id,
            data=agendamento.data,
            hora_inicio=agendamento.hora_inicio,
            hora_termino=agendamento.hora_termino,
            observacoes=agendamento.observacoes,
            status=agendamento.status.value if hasattr(agendamento.status, 'value') else agendamento.status,
            usuario_id=agendamento.usuario_id,
            aeronave_id=agendamento.aeronave_id,
            aeroclube_id=agendamento.aeroclube_id,
            aeroclube_nome=agendamento.aeroclube_rel.nome if agendamento.aeroclube_rel else None,
            solicitante_nome=agendamento.solicitante.nome_completo if agendamento.solicitante else None,
            aeronave_matricula=agendamento.aeronave.matricula if agendamento.aeronave else None,
            aeronave_modelo=agendamento.aeronave.modelo if agendamento.aeronave else None,
            tempo_balizamento_minutos=round(dif, 1) if dif else None,
            created_at=agendamento.created_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{agendamento_id}", response_model=AgendamentoResponse)
async def atualizar_agendamento(
    agendamento_id: int,
    data: AgendamentoUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: Usuario = Depends(get_current_user),
):
    if current_user.nivel_acesso == NivelAcesso.ADMINISTRADOR and data.aeroclube_id is not None and data.aeroclube_id != current_user.aeroclube_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrador só pode agendar no seu próprio aeroclube")
    service = AgendamentoService(session)
    try:
        agendamento = await service.atualizar(agendamento_id, data, current_user.id)
        if not agendamento:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agendamento não encontrado")
        dif = (agendamento.hora_termino - agendamento.hora_inicio).total_seconds() / 60 if agendamento.hora_inicio and agendamento.hora_termino else None

        # Publica atualizacao do agendamento via MQTT
        await _publicar_agendamento_mqtt(agendamento, session)

        return AgendamentoResponse(
            id=agendamento.id,
            data=agendamento.data,
            hora_inicio=agendamento.hora_inicio,
            hora_termino=agendamento.hora_termino,
            observacoes=agendamento.observacoes,
            status=agendamento.status.value if hasattr(agendamento.status, 'value') else agendamento.status,
            usuario_id=agendamento.usuario_id,
            aeronave_id=agendamento.aeronave_id,
            aeroclube_id=agendamento.aeroclube_id,
            aeroclube_nome=agendamento.aeroclube_rel.nome if agendamento.aeroclube_rel else None,
            solicitante_nome=agendamento.solicitante.nome_completo if agendamento.solicitante else None,
            aeronave_matricula=agendamento.aeronave.matricula if agendamento.aeronave else None,
            aeronave_modelo=agendamento.aeronave.modelo if agendamento.aeronave else None,
            tempo_balizamento_minutos=round(dif, 1) if dif else None,
            created_at=agendamento.created_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{agendamento_id}")
async def excluir_agendamento(
    agendamento_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: Usuario = Depends(get_current_user),
):
    service = AgendamentoService(session)
    try:
        # Carrega agendamento com relacoes antes de excluir
        ag_del = await service.obter_por_id(agendamento_id)
        if ag_del:
            await _cancelar_agendamento_mqtt(ag_del, session)

        success = await service.excluir(agendamento_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agendamento não encontrado")

        return {"message": "Agendamento excluído com sucesso"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
