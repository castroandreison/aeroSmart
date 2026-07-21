import asyncio
import json
import threading
from datetime import datetime
from typing import Optional
import paho.mqtt.client as mqtt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.core.database import async_session_factory
from app.services.configuracao_service import ConfiguracaoService
from app.models.alerta import Alerta
from app.models.log import Log
from app.models.agendamento import Agendamento, StatusAgendamento
from app.models.acionamento import Acionamento
from app.models.aeroclube import Aeroclube
from app.models.financeiro import Financeiro
from app.core.timezone import agora_sp


class MqttService:
    def __init__(self):
        self._client: Optional[mqtt.Client] = None
        self._connected = False
        self._lock = threading.Lock()
        self._pending_commands: dict[str, asyncio.Event] = {}
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._heartbeat_cache: dict[str, dict] = {}
        self._heartbeat_client: Optional[mqtt.Client] = None
        self._heartbeat_listener_running = False
        self._lock_heartbeat = threading.Lock()

        self._bal_read_client: Optional[mqtt.Client] = None
        self._bal_read_listener_running = False
        self._lock_bal_read = threading.Lock()

    def _get_loop(self) -> asyncio.AbstractEventLoop:
        if self._loop is None:
            try:
                self._loop = asyncio.get_running_loop()
            except RuntimeError:
                self._loop = asyncio.new_event_loop()
        return self._loop

    async def obter_config(self) -> dict:
        async with async_session_factory() as session:
            svc = ConfiguracaoService(session)
            return {
                "host": await svc.obter("mqtt_broker_host", "localhost"),
                "port": int(await svc.obter("mqtt_broker_port", "1883")),
                "username": await svc.obter("mqtt_username", ""),
                "password": await svc.obter("mqtt_password", ""),
                "topic_prefix": await svc.obter("mqtt_topic_prefix", "Bal"),
                "timeout": int(await svc.obter("mqtt_timeout_segundos", "10")),
            }

    def _on_connect(self, client, userdata, flags, rc):
        self._connected = rc == 0
        print(f"[MQTT] Conectado ao broker" if self._connected else f"[MQTT] Falha na conexão: rc={rc}")

    def _on_disconnect(self, client, userdata, rc):
        self._connected = False

    def _on_message(self, client, userdata, msg):
        payload = msg.payload.decode()
        print(f"[MQTT] Resposta em {msg.topic}: {payload}")
        topic_key = msg.topic
        loop = self._get_loop()
        if topic_key in self._pending_commands:
            event = self._pending_commands.pop(topic_key)
            try:
                loop.call_soon_threadsafe(event.set)
            except Exception:
                pass

    async def conectar(self) -> bool:
        config = await self.obter_config()
        host = config["host"]
        port = config["port"]
        if not host:
            return False

        with self._lock:
            if self._client:
                try:
                    self._client.loop_stop()
                    self._client.disconnect()
                except Exception:
                    pass

            self._client = mqtt.Client()
            self._client.on_connect = self._on_connect
            self._client.on_disconnect = self._on_disconnect
            self._client.on_message = self._on_message

            if config["username"]:
                self._client.username_pw_set(config["username"], config["password"])

        conn_event = threading.Event()
        def on_connect_wrapper(c, u, f, rc):
            self._on_connect(c, u, f, rc)
            conn_event.set()
        self._client.on_connect = on_connect_wrapper

        self._client.connect_async(host, port, 60)
        self._client.loop_start()

        loop = self._get_loop()
        try:
            await asyncio.wait_for(
                loop.run_in_executor(None, conn_event.wait),
                timeout=5,
            )
        except asyncio.TimeoutError:
            print(f"[MQTT] Timeout ao conectar em {host}:{port}")
        except Exception as e:
            print(f"[MQTT] Erro ao conectar: {e}")

        return self._connected

    async def desconectar(self):
        with self._lock:
            if self._client:
                try:
                    self._client.loop_stop()
                    self._client.disconnect()
                except Exception:
                    pass
                self._client = None
                self._connected = False

    async def _executar_com_mqtt(
        self, fn, *args, subscribe_topic: str = None, response_timeout: int = 10, **kwargs
    ):
        config = await self.obter_config()
        host = config["host"]
        port = config["port"]
        username = config["username"]
        password = config["password"]

        client = mqtt.Client()
        response_event = threading.Event()
        response_payload = [None]
        pronto_para_resposta = [False]

        def on_message(c, u, msg):
            payload = msg.payload.decode()
            if subscribe_topic and msg.topic == subscribe_topic and pronto_para_resposta[0]:
                response_payload[0] = payload
                response_event.set()
            print(f"[MQTT] Mensagem em {msg.topic}: {payload}")

        client.on_message = on_message
        if username:
            client.username_pw_set(username, password)

        try:
            loop = self._get_loop()
            await loop.run_in_executor(None, lambda: client.connect(host, port, 60))
        except Exception as e:
            print(f"[MQTT] Falha ao conectar em {host}:{port}: {e}")
            return False
        client.loop_start()

        try:
            if subscribe_topic:
                client.subscribe(subscribe_topic, qos=1)
                await asyncio.sleep(0.3)

            result = fn(client, *args, **kwargs)

            if subscribe_topic:
                pronto_para_resposta[0] = True
                try:
                    await asyncio.wait_for(
                        loop.run_in_executor(None, response_event.wait),
                        timeout=response_timeout,
                    )
                    print(f"[MQTT] Resposta recebida em {subscribe_topic}: {response_payload[0]}")
                    self._ultima_resposta = response_payload[0]
                    return True
                except asyncio.TimeoutError:
                    print(f"[MQTT] Timeout aguardando resposta em {subscribe_topic}")
                    return False
            else:
                await asyncio.sleep(0.5)
                return result
        finally:
            try:
                client.loop_stop()
                client.disconnect()
            except Exception:
                pass

    async def publicar(self, topic: str, payload: str) -> bool:
        def _pub(client):
            client.publish(topic, payload, qos=1)
            print(f"[MQTT] Publicado {payload} em {topic}")
            return True
        return await self._executar_com_mqtt(_pub)

    async def enviar_comando_balizador(
        self, aeroclube_id: int, aeroclube_nome: str, ligar: bool, wait_response: bool = True, session: Optional[AsyncSession] = None,
        agendamento_info: Optional[dict] = None
    ) -> bool:
        try:
            config = await self.obter_config()
            timeout = config["timeout"]
            prefixo = config["topic_prefix"]
            comando = "BalOn" if ligar else "BalOff"
            topic = f"{prefixo}/Write/{aeroclube_nome}"
            response_topic = f"{prefixo}/Read/{aeroclube_nome}"

            if agendamento_info:
                payload_dict: dict = {"comando": comando, "agendamento": agendamento_info}
                payload_str = json.dumps(payload_dict, ensure_ascii=False)
                log_payload = payload_dict
            else:
                payload_str = comando
                log_payload = comando

            def _envio(client):
                client.publish(topic, payload_str, qos=1)
                print(f"[MQTT] Publicado {comando} em {topic}" + (f", aguardando resposta em {response_topic}" if wait_response else ""))
                return True

            ok = await self._executar_com_mqtt(
                _envio, subscribe_topic=response_topic if wait_response else None, response_timeout=timeout
            )
            if not wait_response:
                ok = True

            now = agora_sp()
            log = Log(
                acao="publicar",
                entidade="mqtt_comando",
                entidade_id=agendamento_info.get("id") if agendamento_info else aeroclube_id,
                descricao=f"Comando {comando} -> {topic} {'OK' if ok else 'FALHA'}",
                detalhes={
                    "topic": topic,
                    "payload": log_payload,
                    "aeroclube_id": aeroclube_id,
                    "aeroclube_nome": aeroclube_nome,
                    "confirmado": ok,
                    "timestamp": now.isoformat() + "Z",
                },
            )

            async def _persistir(s: AsyncSession):
                s.add(log)
                if not ok:
                    alerta = Alerta(
                        estacao=aeroclube_nome,
                        comando=comando,
                        mensagem=f"Balizador {aeroclube_nome} não respondeu ao comando {comando}",
                        lido=False,
                    )
                    s.add(alerta)
                    print(f"[MQTT] Alerta para {aeroclube_nome}: sem resposta ao {comando}")
                await s.commit()

            if session is not None:
                await _persistir(session)
            else:
                async with async_session_factory() as s:
                    await _persistir(s)

            return ok
        except Exception as e:
            print(f"[MQTT] ERRO em enviar_comando_balizador: {e}")
            import traceback
            traceback.print_exc()
            return False


    async def enviar_agendamento(self, aeroclube_id: int, aeroclube_nome: str, agendamento_data: dict) -> bool:
        """Envia dados completos do agendamento para a estacao via MQTT"""
        config = await self.obter_config()
        prefixo = config["topic_prefix"]
        topic = f"{prefixo}/Write/{aeroclube_nome}"
        payload_dict = {"comando": "AgendarBalizamento", "agendamento": agendamento_data}
        payload_str = json.dumps(payload_dict, ensure_ascii=False)

        def _envio(client):
            client.publish(topic, payload_str, qos=1)
            print(f"[MQTT] Agendamento enviado para {topic}")
            return True

        return await self._executar_com_mqtt(_envio, response_timeout=5)

    async def enviar_cancelamento_agendamento(self, aeroclube_id: int, aeroclube_nome: str, agendamento_id: int) -> bool:
        """Envia cancelamento de agendamento para a estacao"""
        config = await self.obter_config()
        prefixo = config["topic_prefix"]
        topic = f"{prefixo}/Write/{aeroclube_nome}"
        payload_dict = {"comando": "CancelarAgendamento", "agendamento": {"id": agendamento_id}}
        payload_str = json.dumps(payload_dict, ensure_ascii=False)

        def _envio(client):
            client.publish(topic, payload_str, qos=1)
            print(f"[MQTT] Cancelamento de agendamento {agendamento_id} enviado para {topic}")
            return True

        return await self._executar_com_mqtt(_envio, response_timeout=5)

    async def request_heartbeat(self, aeroclube_id: int, aeroclube_nome: str, timeout: int = 10) -> Optional[dict]:
        """Solicita heartbeat da estacao e retorna o JSON de resposta"""
        config = await self.obter_config()
        topic = f"{config['topic_prefix']}/Write/{aeroclube_nome}"
        response_topic = f"Heartbeat/{aeroclube_nome}"
        payload_str = json.dumps({"comando": "RequestHeartbeat"})

        def _envio(client):
            client.publish(topic, payload_str, qos=1)
            print(f"[MQTT] Solicitando heartbeat em {topic}")
            return True

        # Subscribe to Heartbeat topic to catch the response
        ok = await self._executar_com_mqtt(_envio, subscribe_topic=response_topic, response_timeout=timeout)

        resposta = None
        if ok and self._ultima_resposta:
            try:
                resposta = json.loads(self._ultima_resposta)
            except json.JSONDecodeError:
                pass

        return resposta

    async def ler_energia(self, aeroclube_nome: str) -> Optional[dict]:
        self._ultima_resposta = None
        config = await self.obter_config()
        timeout = config["timeout"]
        comando = "ReadRegistersEnergy"
        topic = f"SDM120/Write/{aeroclube_nome}"
        response_topic = f"SDM120/Read/{aeroclube_nome}"
        payload_str = json.dumps({"comando": comando}, ensure_ascii=False)

        def _envio(client):
            client.publish(topic, payload_str, qos=1)
            print(f"[MQTT] Publicado {payload_str} em {topic}, aguardando resposta em {response_topic}")
            return True

        ok = await self._executar_com_mqtt(
            _envio, subscribe_topic=response_topic, response_timeout=timeout
        )

        resposta = None
        if ok and self._ultima_resposta:
            try:
                resposta = json.loads(self._ultima_resposta)
            except json.JSONDecodeError:
                pass

        now = agora_sp()
        detalhes = {
            "topic": topic,
            "payload": comando,
            "aeroclube_nome": aeroclube_nome,
            "confirmado": ok,
            "timestamp": now.isoformat() + "Z",
        }
        if resposta:
            detalhes["resposta"] = {
                "status": resposta.get("status"),
                "registradores": resposta.get("registradores"),
                "equipamento": resposta.get("equipamento"),
            }

        log = Log(
            acao="publicar",
            entidade="mqtt_energia",
            descricao=f"Comando {comando} -> {topic} {'OK' if ok else 'FALHA'}",
            detalhes=detalhes,
        )
        try:
            async with async_session_factory() as s:
                s.add(log)
                if resposta is None or not resposta.get("registradores"):
                    alerta = Alerta(
                        estacao=aeroclube_nome,
                        comando="ReadRegistersEnergy",
                        mensagem="Falha - sem resposta do medidor" if resposta is None else "Falha - resposta sem registradores",
                        lido=False,
                    )
                    s.add(alerta)
                await s.commit()
        except Exception as e:
            print(f"[MQTT] ERRO ao salvar log/alerta energia: {e}")

        return resposta


    async def start_heartbeat_listener(self):
        if self._heartbeat_listener_running:
            return
        config = await self.obter_config()
        host = config["host"]
        port = config["port"]
        username = config["username"]
        password = config["password"]
        if not host:
            print("[MQTT Heartbeat] Broker não configurado")
            return

        def _on_connect_hb(c, u, f, rc):
            if rc == 0:
                c.subscribe("Heartbeat/+", qos=1)
                print("[MQTT Heartbeat] Conectado e inscrito em Heartbeat/+")
            else:
                print(f"[MQTT Heartbeat] Falha conexão: rc={rc}")

        def _on_message_hb(c, u, msg):
            try:
                payload = json.loads(msg.payload.decode())
                station_name = msg.topic.split("/", 1)[1] if "/" in msg.topic else msg.topic
                with self._lock_heartbeat:
                    self._heartbeat_cache[station_name] = payload
                print(f"[MQTT Heartbeat] Cache atualizado para {station_name}")
            except Exception as e:
                print(f"[MQTT Heartbeat] Erro processando {msg.topic}: {e}")

        with self._lock:
            if self._heartbeat_client:
                try:
                    self._heartbeat_client.loop_stop()
                    self._heartbeat_client.disconnect()
                except Exception:
                    pass
            self._heartbeat_client = mqtt.Client()
            self._heartbeat_client.on_connect = _on_connect_hb
            self._heartbeat_client.on_message = _on_message_hb
            if username:
                self._heartbeat_client.username_pw_set(username, password)
            try:
                self._heartbeat_client.connect_async(host, port, 60)
                self._heartbeat_client.loop_start()
                self._heartbeat_listener_running = True
                print(f"[MQTT Heartbeat] Listener iniciado em {host}:{port}")
            except Exception as e:
                print(f"[MQTT Heartbeat] Erro ao iniciar: {e}")

    def stop_heartbeat_listener(self):
        with self._lock:
            if self._heartbeat_client:
                try:
                    self._heartbeat_client.loop_stop()
                    self._heartbeat_client.disconnect()
                except Exception:
                    pass
                self._heartbeat_client = None
            self._heartbeat_listener_running = False
            print("[MQTT Heartbeat] Listener parado")

    def get_cached_heartbeat(self, station_name: str) -> Optional[dict]:
        with self._lock_heartbeat:
            return self._heartbeat_cache.get(station_name)

    def get_all_cached_heartbeats(self) -> dict[str, dict]:
        with self._lock_heartbeat:
            return dict(self._heartbeat_cache)

    async def _process_bal_read_message(self, topic: str, payload: dict):
        try:
            station_name = topic.split("/", 2)[2] if topic.count("/") >= 2 else topic.split("/", 1)[1]
            comando = payload.get("comando")
            ag = payload.get("agendamento", {})
            ag_id = ag.get("id")
            print(f"[MQTT BalRead] {comando} id={ag_id} estacao={station_name}")

            async with async_session_factory() as session:
                if comando == "AgendamentoConfirmado":
                    if not ag_id:
                        return
                    await session.execute(
                        update(Agendamento)
                        .where(Agendamento.id == ag_id)
                        .values(status=StatusAgendamento.CONFIRMADO, updated_at=agora_sp())
                    )
                    await session.commit()
                    print(f"[MQTT BalRead] Agendamento {ag_id} confirmado")

                elif comando in ("AgendamentoAndamento", "AgendamentoFinalizado"):
                    if not ag_id:
                        return
                    await self._atualizar_agendamento_status(session, ag_id, comando, payload)

                elif comando in ("BalOff", "ConsumoBalizamento"):
                    await self._finalizar_agendamento_estacao(session, station_name, comando, payload)
        except Exception as e:
            print(f"[MQTT BalRead] Erro processando {topic}: {type(e).__name__}: {e}")

    async def _atualizar_agendamento_status(self, session, ag_id, comando, payload):
        now = agora_sp()
        if comando == "AgendamentoAndamento":
            result = await session.execute(
                select(Acionamento).where(Acionamento.agendamento_id == ag_id)
            )
            acionamento = result.scalar_one_or_none()
            if not acionamento:
                acionamento = Acionamento(
                    agendamento_id=ag_id,
                    data_hora_ligamento=now,
                    status="ligado",
                    confirmado=True,
                )
                session.add(acionamento)
            else:
                acionamento.status = "ligado"
                acionamento.confirmado = True

            await session.execute(
                update(Agendamento)
                .where(Agendamento.id == ag_id)
                .values(status=StatusAgendamento.EM_ANDAMENTO, updated_at=now)
            )
            await session.commit()
            print(f"[MQTT BalRead] Agendamento {ag_id} em andamento")

        elif comando == "AgendamentoFinalizado":
            result = await session.execute(
                select(Acionamento).where(Acionamento.agendamento_id == ag_id)
            )
            acionamento = result.scalar_one_or_none()
            if acionamento and not acionamento.data_hora_desligamento:
                acionamento.data_hora_desligamento = now
                acionamento.data_hora_ligamento = acionamento.data_hora_ligamento or now
                acionamento.tempo_ligado_segundos = (
                    now - acionamento.data_hora_ligamento
                ).total_seconds()
                acionamento.status = "desligado"

            ag_result = await session.execute(
                select(Agendamento).where(Agendamento.id == ag_id).options(
                    selectinload(Agendamento.acionamento),
                    selectinload(Agendamento.financeiro)
                )
            )
            ag = ag_result.scalar_one_or_none()

            await session.execute(
                update(Agendamento)
                .where(Agendamento.id == ag_id)
                .values(status=StatusAgendamento.CONCLUIDO, updated_at=now)
            )
            await session.commit()

            if ag and not ag.financeiro:
                from app.services.financeiro_service import FinanceiroService
                financeiro_svc = FinanceiroService(session)
                ac = ag.acionamento
                if ac and ac.tempo_ligado_segundos:
                    tempo_min = ac.tempo_ligado_segundos / 60
                else:
                    diff = (ag.hora_termino - ag.hora_inicio).total_seconds()
                    tempo_min = max(diff / 60, 0)
                if tempo_min > 0:
                    await financeiro_svc.registrar_financeiro(ag.id, tempo_min, ag.aeroclube_id)

            print(f"[MQTT BalRead] Agendamento {ag_id} finalizado")

    async def _finalizar_agendamento_estacao(self, session, station_name, comando, payload):
        try:
            result = await session.execute(
                select(Agendamento)
                .join(Aeroclube, Aeroclube.id == Agendamento.aeroclube_id)
                .where(Aeroclube.nome == station_name)
                .where(Agendamento.status == StatusAgendamento.EM_ANDAMENTO)
                .order_by(Agendamento.id.desc())
                .limit(1)
            )
            ag = result.scalar_one_or_none()
            if not ag:
                print(f"[MQTT BalRead] Nenhum agendamento EM_ANDAMENTO para {station_name}")
                return

            now = agora_sp()
            result_ac = await session.execute(
                select(Acionamento).where(Acionamento.agendamento_id == ag.id)
            )
            acionamento = result_ac.scalar_one_or_none()

            if comando == "ConsumoBalizamento":
                if acionamento and not acionamento.data_hora_desligamento:
                    acionamento.data_hora_desligamento = now
                    duracao = payload.get("duracao_segundos", 0)
                    acionamento.tempo_ligado_segundos = duracao or (
                        now - acionamento.data_hora_ligamento
                    ).total_seconds()
                    acionamento.status = "desligado"
                    acionamento.confirmado = True
            else:
                if acionamento and not acionamento.data_hora_desligamento:
                    acionamento.data_hora_desligamento = now
                    acionamento.tempo_ligado_segundos = (
                        now - acionamento.data_hora_ligamento
                    ).total_seconds()
                    acionamento.status = "desligado"

            await session.execute(
                update(Agendamento)
                .where(Agendamento.id == ag.id)
                .values(status=StatusAgendamento.CONCLUIDO, updated_at=now)
            )
            await session.commit()

            from app.services.financeiro_service import FinanceiroService
            financeiro_svc = FinanceiroService(session)
            fin_result = await session.execute(select(Financeiro).where(Financeiro.agendamento_id == ag.id))
            if not fin_result.scalar_one_or_none():
                ac = acionamento
                if ac and ac.tempo_ligado_segundos:
                    tempo_min = ac.tempo_ligado_segundos / 60
                else:
                    diff = (ag.hora_termino - ag.hora_inicio).total_seconds()
                    tempo_min = max(diff / 60, 0)
                if tempo_min > 0:
                    await financeiro_svc.registrar_financeiro(ag.id, tempo_min, ag.aeroclube_id)

            print(f"[MQTT BalRead] Estacao {station_name} desligada via {comando}, agendamento {ag.id} concluido")
        except Exception as e:
            print(f"[MQTT BalRead] Erro finalizar estacao {station_name}: {type(e).__name__}: {e}")

    async def start_bal_read_listener(self):
        if self._bal_read_listener_running:
            return
        config = await self.obter_config()
        host = config["host"]
        port = config["port"]
        username = config["username"]
        password = config["password"]
        prefixo = config["topic_prefix"]
        if not host:
            print("[MQTT BalRead] Broker nao configurado")
            return

        subscribe_topic = f"{prefixo}/Read/+"

        def _on_connect_br(c, u, f, rc):
            if rc == 0:
                c.subscribe(subscribe_topic, qos=1)
                print(f"[MQTT BalRead] Conectado e inscrito em {subscribe_topic}")
            else:
                print(f"[MQTT BalRead] Falha conexao: rc={rc}")

        def _on_message_br(c, u, msg):
            try:
                payload = json.loads(msg.payload.decode())
                loop = self._get_loop()
                asyncio.run_coroutine_threadsafe(
                    self._process_bal_read_message(msg.topic, payload), loop
                )
            except Exception as e:
                print(f"[MQTT BalRead] Erro no callback: {e}")

        with self._lock_bal_read:
            if self._bal_read_client:
                try:
                    self._bal_read_client.loop_stop()
                    self._bal_read_client.disconnect()
                except Exception:
                    pass
            self._bal_read_client = mqtt.Client()
            self._bal_read_client.on_connect = _on_connect_br
            self._bal_read_client.on_message = _on_message_br
            if username:
                self._bal_read_client.username_pw_set(username, password)
            try:
                self._bal_read_client.connect_async(host, port, 60)
                self._bal_read_client.loop_start()
                self._bal_read_listener_running = True
                print(f"[MQTT BalRead] Listener iniciado em {host}:{port} -> {subscribe_topic}")
            except Exception as e:
                print(f"[MQTT BalRead] Erro ao iniciar: {e}")

    def stop_bal_read_listener(self):
        with self._lock_bal_read:
            if self._bal_read_client:
                try:
                    self._bal_read_client.loop_stop()
                    self._bal_read_client.disconnect()
                except Exception:
                    pass
                self._bal_read_client = None
            self._bal_read_listener_running = False
            print("[MQTT BalRead] Listener parado")


mqtt_service = MqttService()
