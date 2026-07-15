from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.database import get_session
from app.core.security import get_current_user, verificar_admin_ou_proprietario
from app.models.usuario import Usuario
from app.models.controlador import Controlador
from app.models.agendamento import Agendamento, StatusAgendamento
from app.services.automacao_service import AutomacaoService
from app.services.agendamento_service import AgendamentoService
from sqlalchemy import select

router = APIRouter(prefix="/automacao", tags=["Automação"])


@router.get("/status")
async def get_status_automacao(
    session: AsyncSession = Depends(get_session),
    current_user: Usuario = Depends(get_current_user),
):
    automacao = AutomacaoService(session)
    return await automacao.get_status_pista()


@router.post("/testar-ligamento/{agendamento_id}")
async def testar_ligamento(
    agendamento_id: int,
    session: AsyncSession = Depends(get_session),
    admin: Usuario = Depends(verificar_admin_ou_proprietario),
):
    automacao = AutomacaoService(session)
    success = await automacao.ligar_pista(agendamento_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Falha ao ligar pista")
    return {"message": "Pista ligada com sucesso"}


@router.post("/testar-desligamento/{agendamento_id}")
async def testar_desligamento(
    agendamento_id: int,
    session: AsyncSession = Depends(get_session),
    admin: Usuario = Depends(verificar_admin_ou_proprietario),
):
    automacao = AutomacaoService(session)
    success = await automacao.desligar_pista(agendamento_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Falha ao desligar pista")
    return {"message": "Pista desligada com sucesso"}


@router.post("/confirmar-balon/{agendamento_id}")
async def confirmar_balon(
    agendamento_id: int,
    confirmado: bool = True,
    session: AsyncSession = Depends(get_session),
    admin: Usuario = Depends(verificar_admin_ou_proprietario),
):
    """Atualiza status do agendamento para CONFIRMADO quando recebe confirmação MQTT do BalOn"""
    service = AgendamentoService(session)
    agendamento = await service.obter_por_id(agendamento_id)
    if not agendamento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agendamento não encontrado")
    if confirmado:
        agendamento.status = StatusAgendamento.CONFIRMADO
    else:
        agendamento.status = StatusAgendamento.AGENDADO
    await session.commit()
    return {"message": f"Agendamento {'confirmado' if confirmado else 'voltou para agendado'}", "status": agendamento.status.value}


@router.post("/finalizar-baloff/{agendamento_id}")
async def finalizar_baloff(
    agendamento_id: int,
    confirmado: bool = True,
    session: AsyncSession = Depends(get_session),
    admin: Usuario = Depends(verificar_admin_ou_proprietario),
):
    """Atualiza status do agendamento para CONCLUIDO quando recebe confirmação MQTT do BalOff"""
    service = AgendamentoService(session)
    agendamento = await service.obter_por_id(agendamento_id)
    if not agendamento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agendamento não encontrado")
    if confirmado:
        agendamento.status = StatusAgendamento.CONCLUIDO
    await session.commit()
    return {"message": "Agendamento concluído", "status": agendamento.status.value}


@router.get("/controladores")
async def listar_controladores(
    session: AsyncSession = Depends(get_session),
    admin: Usuario = Depends(verificar_admin_ou_proprietario),
):
    result = await session.execute(select(Controlador).order_by(Controlador.nome))
    return list(result.scalars().all())


@router.post("/controladores")
async def criar_controlador(
    data: dict,
    session: AsyncSession = Depends(get_session),
    admin: Usuario = Depends(verificar_admin_ou_proprietario),
):
    controlador = Controlador(**data)
    session.add(controlador)
    await session.commit()
    await session.refresh(controlador)
    return controlador


@router.post("/finalizar-agendamentos-passados")
async def finalizar_agendamentos_passados(
    session: AsyncSession = Depends(get_session),
    admin: Usuario = Depends(verificar_admin_ou_proprietario),
):
    """Conclui agendamentos que já passaram da hora de término e não estão concluídos/cancelados"""
    from app.services.agendamento_service import AgendamentoService
    service = AgendamentoService(session)
    count = await service.finalizar_agendamentos_passados()
    return {"message": f"{count} agendamentos finalizados", "count": count}


@router.post("/atualizar-status-por-tempo")
async def atualizar_status_por_tempo(
    session: AsyncSession = Depends(get_session),
    admin: Usuario = Depends(verificar_admin_ou_proprietario),
):
    """Atualiza status dos agendamentos baseado no horário atual:
    - AGENDADO/CONFIRMADO -> EM_ANDAMENTO (se agora entre hora_inicio e hora_termino)
    - EM_ANDAMENTO -> CONCLUIDO (se agora > hora_termino)
    """
    automacao = AutomacaoService(session)
    result = await automacao.atualizar_status_por_tempo()
    return {"message": "Status atualizados", **result}
