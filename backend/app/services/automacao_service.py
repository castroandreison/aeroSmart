from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import Optional
from datetime import datetime
import httpx
import json
import asyncio

from app.core.timezone import agora_sp
from app.models.controlador import Controlador
from app.models.acionamento import Acionamento
from app.models.agendamento import Agendamento, StatusAgendamento
from app.models.usuario import Usuario
from app.models.aeroclube import Aeroclube
from app.services.configuracao_service import ConfiguracaoService
from app.services.log_service import LogService
from app.services.mqtt_service import mqtt_service


class AutomacaoService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.config_service = ConfiguracaoService(session)
        self.log_service = LogService(session)

    async def obter_controlador_ativo(self) -> Optional[Controlador]:
        result = await self.session.execute(
            select(Controlador).where(Controlador.ativo == True).limit(1)
        )
        return result.scalar_one_or_none()

    async def _obter_aeroclube_do_agendamento(self, agendamento_id: int) -> tuple[Optional[int], Optional[str]]:
        result = await self.session.execute(
            select(Agendamento)
            .options(selectinload(Agendamento.solicitante).selectinload(Usuario.aeroclube_rel))
            .where(Agendamento.id == agendamento_id)
        )
        ag = result.scalar_one_or_none()
        if ag and ag.solicitante and ag.solicitante.aeroclube_rel:
            return ag.solicitante.aeroclube_rel.id, ag.solicitante.aeroclube_rel.nome
        return None, None

    async def ligar_pista(self, agendamento_id: int) -> bool:
        # Verifica se ja existe acionamento para este agendamento
        result = await self.session.execute(
            select(Acionamento).where(Acionamento.agendamento_id == agendamento_id)
        )
        acionamento = result.scalar_one_or_none()

        if not acionamento:
            acionamento = Acionamento(
                agendamento_id=agendamento_id,
                data_hora_ligamento=agora_sp(),
                status="ligando",
            )
            self.session.add(acionamento)

        # Envia comando MQTT BalOn para o balizador do aeroclube
        aero_id, aero_nome = await self._obter_aeroclube_do_agendamento(agendamento_id)

        # Obtem dados do agendamento para incluir na mensagem MQTT
        ag_result = await self.session.execute(
            select(Agendamento).where(Agendamento.id == agendamento_id)
        )
        ag_obj = ag_result.scalar_one_or_none()
        ag_info = None
        if ag_obj:
            duracao = (ag_obj.hora_termino - ag_obj.hora_inicio).total_seconds() / 60
            ag_info = {
                "id": ag_obj.id,
                "data": ag_obj.data.isoformat() if hasattr(ag_obj.data, 'isoformat') else str(ag_obj.data),
                "horario": ag_obj.hora_inicio.strftime("%H:%M"),
                "hora_termino": ag_obj.hora_termino.strftime("%H:%M"),
                "duracao_minutos": round(duracao),
            }

        mqtt_ok = False
        if aero_id and aero_nome:
            mqtt_ok = await mqtt_service.enviar_comando_balizador(aero_id, aero_nome, ligar=True, wait_response=True, session=self.session, agendamento_info=ag_info)

        controlador = await self.obter_controlador_ativo()
        try:
            if controlador and controlador.tipo == "http":
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        controlador.endpoint + "/ligar",
                        json={"agendamento_id": agendamento_id},
                        timeout=10,
                    )
                    response.raise_for_status()
                controlador.ultimo_status = "online"
                controlador.ultima_comunicacao = agora_sp()

            acionamento.status = "ligado" if mqtt_ok else "falha"
            acionamento.confirmado = mqtt_ok

            await self.session.execute(
                update(Agendamento)
                .where(Agendamento.id == agendamento_id)
                .values(
                    status=StatusAgendamento.EM_ANDAMENTO if mqtt_ok else StatusAgendamento.FALHA,
                    updated_at=agora_sp()
                )
            )

            await self.session.commit()
            return mqtt_ok

        except Exception as e:
            acionamento.status = "falha"
            await self.session.commit()
            return False

    async def desligar_pista(self, agendamento_id: int) -> bool:
        result = await self.session.execute(
            select(Acionamento).where(Acionamento.agendamento_id == agendamento_id)
        )
        acionamento = result.scalar_one_or_none()
        if not acionamento:
            return False

        # Envia comando MQTT BalOff para o balizador do aeroclube
        aero_id, aero_nome = await self._obter_aeroclube_do_agendamento(agendamento_id)

        # Obtem dados do agendamento para incluir na mensagem MQTT
        ag_result = await self.session.execute(
            select(Agendamento).where(Agendamento.id == agendamento_id)
        )
        ag_obj = ag_result.scalar_one_or_none()
        ag_info = None
        if ag_obj:
            duracao = (ag_obj.hora_termino - ag_obj.hora_inicio).total_seconds() / 60
            ag_info = {
                "id": ag_obj.id,
                "data": ag_obj.data.isoformat() if hasattr(ag_obj.data, 'isoformat') else str(ag_obj.data),
                "horario": ag_obj.hora_inicio.strftime("%H:%M"),
                "hora_termino": ag_obj.hora_termino.strftime("%H:%M"),
                "duracao_minutos": round(duracao),
            }

        mqtt_ok = False
        if aero_id and aero_nome:
            mqtt_ok = await mqtt_service.enviar_comando_balizador(aero_id, aero_nome, ligar=False, session=self.session, agendamento_info=ag_info)

        # Se MQTT falhou, pode ser que a estacao ja finalizou sozinha
        fallback_ok = False
        if not mqtt_ok and aero_id and aero_nome:
            print(f"[automacao] BalOff falhou, verificando status da estacao {aero_nome}...")
            try:
                hb = await mqtt_service.request_heartbeat(aero_id, aero_nome, timeout=8)
                if hb and hb.get("balizamento", {}).get("status") == "Inativo":
                    fallback_ok = True
                    print(f"[automacao] Estacao ja estava desligada, tratando como sucesso")
            except Exception:
                pass

        controlador = await self.obter_controlador_ativo()
        try:
            if controlador and controlador.tipo == "http":
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        controlador.endpoint + "/desligar",
                        json={"agendamento_id": agendamento_id},
                        timeout=10,
                    )
                    response.raise_for_status()
                    controlador.ultimo_status = "online"
                    controlador.ultima_comunicacao = agora_sp()

            now = agora_sp()
            acionamento.data_hora_desligamento = now
            acionamento.tempo_ligado_segundos = (now - acionamento.data_hora_ligamento).total_seconds()
            sucesso = mqtt_ok or fallback_ok
            acionamento.status = "desligado" if sucesso else "falha_desligamento"
            acionamento.confirmado = sucesso

            # Atualiza status do agendamento via UPDATE direto para evitar cache ORM
            await self.session.execute(
                update(Agendamento)
                .where(Agendamento.id == agendamento_id)
                .values(
                    status=StatusAgendamento.CONCLUIDO if sucesso else StatusAgendamento.AGUARDANDO_ENCERRAMENTO,
                    updated_at=agora_sp()
                )
            )

            await self.session.commit()
            return sucesso

        except Exception as e:
            acionamento.status = "falha_desligamento"
            await self.session.commit()
            return False

    async def verificar_pista_ligada(self) -> dict:
        controlador = await self.obter_controlador_ativo()
        if not controlador:
            return {"status": "desconhecido", "controlador_online": False}

        try:
            if controlador.tipo == "http":
                async with httpx.AsyncClient() as client:
                    response = await client.get(controlador.endpoint + "/status", timeout=5)
                    data = response.json()
                    controlador.ultimo_status = "online"
                    controlador.ultima_comunicacao = agora_sp()
                    await self.session.commit()
                    return {**data, "controlador_online": True}
            return {"status": "desconhecido", "controlador_online": True}
        except Exception:
            controlador.ultimo_status = "offline"
            await self.session.commit()
            return {"status": "offline", "controlador_online": False}

    async def get_status_pista(self) -> dict:
        now = agora_sp()

        # Proximo agendamento
        prox_result = await self.session.execute(
            select(Agendamento).where(
                Agendamento.hora_inicio > now,
                Agendamento.status.in_([StatusAgendamento.AGENDADO, StatusAgendamento.CONFIRMADO]),
            ).order_by(Agendamento.hora_inicio).limit(1)
        )
        proximo = prox_result.scalar_one_or_none()

        # Ultimo acionamento ativo
        result = await self.session.execute(
            select(Acionamento).where(
                Acionamento.status.in_(["ligado", "ligando"])
            ).order_by(Acionamento.id.desc()).limit(1)
        )
        acionamento = result.scalar_one_or_none()

        base = {
            "proximo_agendamento": proximo.hora_inicio.isoformat() + "Z" if proximo else None,
            "proximo_agendamento_id": proximo.id if proximo else None,
        }

        if not acionamento:
            # Buscar ultimo acionamento concluido
            ult = await self.session.execute(
                select(Acionamento).order_by(Acionamento.id.desc()).limit(1)
            )
            ultimo = ult.scalar_one_or_none()
            return {
                **base,
                "status": "desligado",
                "tempo_ligado_segundos": 0,
                "tempo_restante_segundos": 0,
                "ultimo_comando": ultimo.status if ultimo else None,
                "ultimo_confirmado": ultimo.confirmado if ultimo else None,
                "comando_confirmado": None,
            }

        tempo_ligado = (now - acionamento.data_hora_ligamento).total_seconds()

        agendamento_result = await self.session.execute(
            select(Agendamento).where(Agendamento.id == acionamento.agendamento_id)
        )
        agendamento = agendamento_result.scalar_one_or_none()

        tempo_restante = 0
        if agendamento:
            tempo_restante = (agendamento.hora_termino - now).total_seconds()

        return {
            **base,
            "status": acionamento.status,
            "comando_confirmado": acionamento.confirmado,
            "tempo_ligado_segundos": tempo_ligado,
            "tempo_restante_segundos": max(0, tempo_restante),
            "agendamento_id": acionamento.agendamento_id,
            "ultimo_comando": acionamento.status,
            "ultimo_confirmado": acionamento.confirmado,
        }

    async def atualizar_status_por_tempo(self) -> dict:
        """Atualiza status dos agendamentos baseado no horário atual"""
        now = agora_sp()
        
        # Agendamentos que já passaram da hora de término -> CONCLUIDO
        finalizados_result = await self.session.execute(
            select(Agendamento).where(
                Agendamento.hora_termino < now,
                Agendamento.status.notin_([StatusAgendamento.CONCLUIDO, StatusAgendamento.AGUARDANDO_ENCERRAMENTO, StatusAgendamento.FALHA, StatusAgendamento.CANCELADO]),
            )
        )
        finalizados = list(finalizados_result.scalars().all())
        for ag in finalizados:
            ag.status = StatusAgendamento.CONCLUIDO
        
        # Agendamentos que já iniciaram mas não terminaram -> EM_ANDAMENTO
        andamento_result = await self.session.execute(
            select(Agendamento).where(
                Agendamento.hora_inicio <= now,
                Agendamento.hora_termino > now,
                Agendamento.status.in_([StatusAgendamento.AGENDADO, StatusAgendamento.CONFIRMADO]),
            )
        )
        em_andamento = list(andamento_result.scalars().all())
        for ag in em_andamento:
            ag.status = StatusAgendamento.EM_ANDAMENTO
        
        if finalizados or em_andamento:
            await self.session.commit()
        
        return {
            "finalizados": len(finalizados),
            "em_andamento": len(em_andamento),
            "total_atualizados": len(finalizados) + len(em_andamento),
        }

