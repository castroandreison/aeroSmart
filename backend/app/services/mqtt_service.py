import asyncio
import json
import threading
from datetime import datetime
from typing import Optional
import paho.mqtt.client as mqtt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.services.configuracao_service import ConfiguracaoService
from app.models.alerta import Alerta
from app.models.log import Log
from app.core.timezone import agora_sp


class MqttService:
    def __init__(self):
        self._client: Optional[mqtt.Client] = None
        self._connected = False
        self._lock = threading.Lock()
        self._pending_commands: dict[str, asyncio.Event] = {}
        self._loop: Optional[asyncio.AbstractEventLoop] = None

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
                "topic_prefix": await svc.obter("mqtt_topic_prefix", "aeroclube"),
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


mqtt_service = MqttService()
