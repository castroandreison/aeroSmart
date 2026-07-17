from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
from datetime import datetime, timezone, timedelta

from app.core.config import settings
from app.core.database import init_db, async_session_factory, engine
from app.services.configuracao_service import ConfiguracaoService
from app.models.aeroclube import Aeroclube
from app.models.usuario import Usuario
from app.models.agendamento import Agendamento, StatusAgendamento
from app.services.automacao_service import AutomacaoService
from app.services.mqtt_service import mqtt_service
from sqlalchemy import select, text
from app.api.v1 import auth, usuarios, aeronaves, agendamentos, configuracoes, financeiro, monitoramento, logs, automacao, relatorios, aeroclubes, mqtt

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.timezone import agora_sp

background_tasks = set()


async def scheduler_balizamento():
    print("[scheduler] Iniciado")
    while True:
        try:
            async with async_session_factory() as session:
                agora = agora_sp()
                agora_str = agora.strftime("%Y-%m-%d %H:%M:%S.%f")
                svc = AutomacaoService(session)

                # 1. Liga balizadores para agendamentos que comecaram (antes de finalizar)
                result = await session.execute(
                    text("""
                        SELECT a.id FROM agendamentos a
                        LEFT JOIN acionamentos ac ON ac.agendamento_id = a.id
                        WHERE a.hora_inicio <= :now
                          AND a.status = 'AGENDADO'
                          AND ac.id IS NULL
                        LIMIT 5
                    """),
                    {"now": agora_str},
                )
                ligar_ids = [row[0] for row in result.fetchall()]
                for aid in ligar_ids:
                    print(f"[scheduler] Ligando pista para agendamento {aid}")
                    await svc.ligar_pista(aid)

                # 2. Desliga balizadores para agendamentos EM_ANDAMENTO que terminaram
                result = await session.execute(
                    text("""
                        SELECT a.id FROM agendamentos a
                        JOIN acionamentos ac ON ac.agendamento_id = a.id
                        WHERE a.hora_termino <= :now
                          AND a.status = 'EM_ANDAMENTO'
                          AND (ac.status = 'ligado' OR ac.status = 'ligando')
                          AND ac.data_hora_desligamento IS NULL
                        LIMIT 5
                    """),
                    {"now": agora_str},
                )
                desligar_ids = [row[0] for row in result.fetchall()]
                for aid in desligar_ids:
                    print(f"[scheduler] Desligando pista para agendamento {aid}")
                    await svc.desligar_pista(aid)

                # 3. Finaliza agendamentos restantes que passaram do termino
                await session.execute(
                    text("UPDATE agendamentos SET status = 'CONCLUIDO', updated_at = :now WHERE hora_termino <= :now AND status NOT IN ('CONCLUIDO', 'AGUARDANDO_ENCERRAMENTO', 'CANCELADO', 'AGENDADO', 'FALHA')"),
                    {"now": agora_str},
                )
                await session.commit()
        except Exception as e:
            print(f"[scheduler] Erro: {type(e).__name__}: {e}")
        await asyncio.sleep(30)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    async with async_session_factory() as session:
        # --- Migrations: add missing columns ---
        async with engine.connect() as conn:
            for tbl, col, col_type in [
                ("aeroclubes", "topic_write", "VARCHAR(255)"),
                ("aeroclubes", "topic_read", "VARCHAR(255)"),
            ]:
                try:
                    await conn.execute(text(f"ALTER TABLE {tbl} ADD COLUMN {col} {col_type}"))
                    await conn.commit()
                    print(f"[migration] Coluna {tbl}.{col} adicionada")
                except Exception:
                    pass

        cfg = ConfiguracaoService(session)
        await cfg.definir("mqtt_topic_prefix", "Bal", descricao="Prefixo dos tópicos MQTT")
        print("[startup] mqtt_topic_prefix definido como 'Bal'")
        result = await session.execute(select(Aeroclube).where(Aeroclube.topic_write.is_(None)))
        for ac in result.scalars().all():
            ac.topic_write = f"Bal/Write/{ac.nome}"
            ac.topic_read = f"Bal/Read/{ac.nome}"
            print(f"[startup] Tópicos gerados para {ac.nome}: Write={ac.topic_write} Read={ac.topic_read}")
        await session.commit()

        # --- Auto-seed if database is empty ---
        total = (await session.execute(select(Usuario))).scalars().first()
        if not total:
            session.close()
            import seed_dados
            await seed_dados.seed()
            print("[startup] Banco populado com dados iniciais")
    print("[startup] Criando scheduler...", flush=True)
    task = asyncio.create_task(scheduler_balizamento())
    background_tasks.add(task)
    print("[startup] Scheduler criado", flush=True)
    print("[startup] Iniciando listener heartbeat MQTT...", flush=True)
    await mqtt_service.start_heartbeat_listener()
    print("[startup] Iniciando listener Bal/Read MQTT...", flush=True)
    await mqtt_service.start_bal_read_listener()
    yield
    mqtt_service.stop_bal_read_listener()
    mqtt_service.stop_heartbeat_listener()
    task.cancel()
    await task

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

prefix = settings.API_V1_PREFIX
app.include_router(auth.router, prefix=prefix)
app.include_router(usuarios.router, prefix=prefix)
app.include_router(aeronaves.router, prefix=prefix)
app.include_router(agendamentos.router, prefix=prefix)
app.include_router(configuracoes.router, prefix=prefix)
app.include_router(financeiro.router, prefix=prefix)
app.include_router(monitoramento.router, prefix=prefix)
app.include_router(logs.router, prefix=prefix)
app.include_router(automacao.router, prefix=prefix)
app.include_router(relatorios.router, prefix=prefix)
app.include_router(aeroclubes.router, prefix=prefix)
app.include_router(mqtt.router, prefix=prefix)


@app.get("/")
async def root():
    return {"message": "AeroClub API", "version": settings.VERSION}


@app.get("/health")
async def health_check():
    return {"status": "ok"}
