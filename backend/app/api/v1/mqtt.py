from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime

from app.core.database import get_session
from app.core.security import get_current_user, verificar_admin_ou_proprietario
from app.models.usuario import Usuario, NivelAcesso
from app.models.alerta import Alerta
from app.services.configuracao_service import ConfiguracaoService
from app.services.log_service import LogService
from app.services.mqtt_service import mqtt_service

router = APIRouter(prefix="/mqtt", tags=["MQTT"])


@router.get("/config")
async def obter_config_mqtt(
    current_user: Usuario = Depends(verificar_admin_ou_proprietario),
):
    config = await mqtt_service.obter_config()
    return config


@router.put("/config")
async def salvar_config_mqtt(
    data: dict,
    session: AsyncSession = Depends(get_session),
    current_user: Usuario = Depends(verificar_admin_ou_proprietario),
):
    svc = ConfiguracaoService(session)
    mapeamento = {
        "host": "mqtt_broker_host",
        "port": "mqtt_broker_port",
        "username": "mqtt_username",
        "password": "mqtt_password",
        "topic_prefix": "mqtt_topic_prefix",
        "timeout": "mqtt_timeout_segundos",
    }
    for campo, chave in mapeamento.items():
        if campo in data:
            await svc.definir(chave, str(data[campo]))
    return {"message": "Configuração MQTT salva"}


@router.get("/status")
async def status_mqtt(
    current_user: Usuario = Depends(verificar_admin_ou_proprietario),
):
    ok = await mqtt_service.conectar()
    return {"connected": ok}


@router.post("/testar")
async def testar_conexao(
    current_user: Usuario = Depends(verificar_admin_ou_proprietario),
):
    ok = await mqtt_service.conectar()
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Falha ao conectar ao broker MQTT")
    return {"message": "Conexão MQTT bem-sucedida"}


@router.post("/testar-comando")
async def testar_comando(
    data: dict,
    current_user: Usuario = Depends(verificar_admin_ou_proprietario),
):
    ligar = data.get("ligar", True)
    aeroclube_id = data.get("aeroclube_id", 0)
    aeroclube_nome = data.get("aeroclube_nome", "Teste")
    try:
        ok = await mqtt_service.enviar_comando_balizador(aeroclube_id, aeroclube_nome, ligar)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro MQTT: {e}")
    if not ok:
        return {"message": f"Comando {'BalOn' if ligar else 'BalOff'} enviado, mas sem confirmação", "confirmado": False}
    return {"message": f"Comando {'BalOn' if ligar else 'BalOff'} confirmado", "confirmado": True}


@router.get("/alertas")
async def listar_alertas(
    lido: Optional[bool] = None,
    session: AsyncSession = Depends(get_session),
    current_user: Usuario = Depends(verificar_admin_ou_proprietario),
):
    query = select(Alerta).order_by(Alerta.created_at.desc())
    if lido is not None:
        query = query.where(Alerta.lido == lido)
    result = await session.execute(query)
    alertas = []
    for a in result.scalars().all():
        alertas.append({
            "id": a.id,
            "estacao": a.estacao,
            "comando": a.comando,
            "mensagem": a.mensagem,
            "lido": a.lido,
            "created_at": (a.created_at.isoformat() + "Z") if a.created_at else None,
        })
    return alertas


@router.get("/logs")
async def listar_logs_mqtt(
    limit: int = 50,
    session: AsyncSession = Depends(get_session),
    current_user: Usuario = Depends(verificar_admin_ou_proprietario),
):
    from app.models.log import Log
    result = await session.execute(
        select(Log)
        .where(Log.entidade == "mqtt_comando")
        .order_by(Log.created_at.desc())
        .limit(limit)
    )
    logs = result.scalars().all()
    return [
        {
            "id": log.id,
            "descricao": log.descricao,
            "detalhes": log.detalhes,
            "created_at": (log.created_at.isoformat() + "Z") if log.created_at else None,
        }
        for log in logs
    ]


@router.get("/logs-energia")
async def listar_logs_energia(
    limit: int = 50,
    session: AsyncSession = Depends(get_session),
    current_user: Usuario = Depends(verificar_admin_ou_proprietario),
):
    from app.models.log import Log
    result = await session.execute(
        select(Log)
        .where(Log.entidade == "mqtt_energia")
        .order_by(Log.created_at.desc())
        .limit(limit)
    )
    logs = result.scalars().all()
    return [
        {
            "id": log.id,
            "descricao": log.descricao,
            "detalhes": log.detalhes,
            "created_at": (log.created_at.isoformat() + "Z") if log.created_at else None,
        }
        for log in logs
    ]


@router.get("/alertas-energia")
async def listar_alertas_energia(
    session: AsyncSession = Depends(get_session),
    current_user: Usuario = Depends(verificar_admin_ou_proprietario),
):
    result = await session.execute(
        select(Alerta)
        .where(Alerta.comando == "ReadRegistersEnergy")
        .order_by(Alerta.created_at.desc())
    )
    alertas = []
    for a in result.scalars().all():
        status = "Concluído" if "Concluído" in (a.mensagem or "") else "Falha"
        alertas.append({
            "id": a.id,
            "estacao": a.estacao,
            "comando": a.comando,
            "mensagem": a.mensagem,
            "status": status,
            "lido": a.lido,
            "created_at": (a.created_at.isoformat() + "Z") if a.created_at else None,
        })
    return alertas


@router.post("/ler-energia")
async def ler_energia(
    data: dict,
    current_user: Usuario = Depends(verificar_admin_ou_proprietario),
):
    aeroclube_nome = data.get("aeroclube_nome", "AeroClub Central")
    try:
        resposta = await mqtt_service.ler_energia(aeroclube_nome)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro leitura energia: {e}")
    if resposta is None:
        raise HTTPException(status_code=status.HTTP_408_REQUEST_TIMEOUT, detail="Sem resposta do medidor de energia")
    return resposta


@router.put("/alertas/{alerta_id}/ler")
async def marcar_alerta_lido(
    alerta_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: Usuario = Depends(verificar_admin_ou_proprietario),
):
    result = await session.execute(select(Alerta).where(Alerta.id == alerta_id))
    alerta = result.scalar_one_or_none()
    if not alerta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alerta não encontrado")
    await session.delete(alerta)
    await session.commit()
    return {"message": "Alerta apagado"}
