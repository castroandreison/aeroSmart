import asyncio, sys
sys.path.insert(0, '.')
from datetime import datetime, date, timedelta, time
from app.core.database import async_session_factory, init_db
from app.core.security import hash_password
from app.models.usuario import Usuario, NivelAcesso
from app.models.aeroclube import Aeroclube
from app.models.aeronave import Aeronave
from app.models.agendamento import Agendamento, StatusAgendamento
from app.models.configuracao import Configuracao
from app.models.financeiro import Financeiro
from app.services.configuracao_service import ConfiguracaoService


async def seed():
    await init_db()
    async with async_session_factory() as session:
        cfg = ConfiguracaoService(session)
        await cfg.definir("mqtt_topic_prefix", "Bal")

        async def get_or_none(model, **kwargs):
            from sqlalchemy import select
            r = await session.execute(select(model).filter_by(**kwargs))
            return r.scalar_one_or_none()

        # --- AEROCLUBES ---
        ac1 = await get_or_none(Aeroclube, nome="AeroClub Central")
        if not ac1:
            ac1 = Aeroclube(nome="AeroClub Central", topic_write="Bal/Write/AeroClub Central", topic_read="Bal/Read/AeroClub Central")
            session.add(ac1)

        ac2 = await get_or_none(Aeroclube, nome="AeroClub Norte")
        if not ac2:
            ac2 = Aeroclube(nome="AeroClub Norte", topic_write="Bal/Write/AeroClub Norte", topic_read="Bal/Read/AeroClub Norte")
            session.add(ac2)

        ac3 = await get_or_none(Aeroclube, nome="AeroClub Sul")
        if not ac3:
            ac3 = Aeroclube(nome="AeroClub Sul", topic_write="Bal/Write/AeroClub Sul", topic_read="Bal/Read/AeroClub Sul")
            session.add(ac3)
        await session.commit()
        for ac in (ac1, ac2, ac3):
            await session.refresh(ac)

        # --- USUARIOS ---
        usuarios_data = [
            ("Admin Geral", "11111111111", "admin@aeroclub.com", "admin123", NivelAcesso.PROPRIETARIO, ac1),
            ("Administrador Central", "22222222222", "adm.central@aeroclub.com", "adm123", NivelAcesso.ADMINISTRADOR, ac1),
            ("Administrador Norte", "33333333333", "adm.norte@aeroclub.com", "adm123", NivelAcesso.ADMINISTRADOR, ac2),
            ("Carlos Silva", "44444444444", "carlos@aeroclub.com", "123456", NivelAcesso.SOLICITANTE, ac1),
            ("Maria Souza", "55555555555", "maria@aeroclub.com", "123456", NivelAcesso.SOLICITANTE, ac1),
            ("João Pereira", "66666666666", "joao@aeroclub.com", "123456", NivelAcesso.SOLICITANTE, ac1),
            ("Ana Costa", "77777777777", "ana@aeroclub.com", "123456", NivelAcesso.SOLICITANTE, ac2),
            ("Pedro Santos", "88888888888", "pedro@aeroclub.com", "123456", NivelAcesso.SOLICITANTE, ac2),
            ("Lucia Oliveira", "99999999999", "lucia@aeroclub.com", "123456", NivelAcesso.SOLICITANTE, ac3),
            ("Roberto Lima", "10101010101", "roberto@aeroclub.com", "123456", NivelAcesso.SOLICITANTE, ac3),
        ]
        usuarios = []
        for nome, cpf, email, senha, nivel, ac in usuarios_data:
            u = await get_or_none(Usuario, email=email)
            if not u:
                u = Usuario(
                    nome_completo=nome, cpf=cpf, email=email,
                    senha_hash=hash_password(senha), nivel_acesso=nivel,
                    aeroclube_id=ac.id, ativo=True,
                )
                session.add(u)
                await session.flush()
            usuarios.append(u)
        await session.commit()
        for u in usuarios:
            await session.refresh(u)

        # --- AERONAVES ---
        aeronaves_data = [
            ("PT-ABC", "Cessna 172", "Cessna", "Monomotor", ac1, usuarios[3]),
            ("PT-DEF", "Cessna 152", "Cessna", "Monomotor", ac1, usuarios[4]),
            ("PT-GHI", "Piper Seneca", "Piper", "Bimotor", ac1, usuarios[5]),
            ("PT-JKL", "Embraer EMB-202", "Embraer", "Aeronautico", ac2, usuarios[6]),
            ("PT-MNO", "Cessna 210", "Cessna", "Monomotor", ac2, usuarios[7]),
            ("PT-PQR", "Beechcraft Baron", "Beechcraft", "Bimotor", ac3, usuarios[8]),
            ("PT-STU", "Cessna 182", "Cessna", "Monomotor", ac3, usuarios[9]),
        ]
        aeronaves = []
        for mat, mod, fab, tipo, ac, prop in aeronaves_data:
            a = await get_or_none(Aeronave, matricula=mat)
            if not a:
                a = Aeronave(matricula=mat, modelo=mod, fabricante=fab, tipo=tipo, usuario_id=prop.id)
                session.add(a)
                await session.flush()
            aeronaves.append(a)
        await session.commit()

        # --- AGENDAMENTOS ---
        hoje = date.today()
        agendamentos_config = [
            (hoje, time(8,0), time(9,0), usuarios[3], aeronaves[0]),
            (hoje, time(9,30), time(10,30), usuarios[4], aeronaves[1]),
            (hoje, time(14,0), time(15,0), usuarios[5], aeronaves[2]),
            (hoje + timedelta(1), time(8,0), time(9,0), usuarios[3], aeronaves[0]),
            (hoje + timedelta(1), time(10,0), time(11,0), usuarios[6], aeronaves[3]),
            (hoje + timedelta(1), time(14,0), time(15,0), usuarios[7], aeronaves[4]),
            (hoje + timedelta(2), time(7,0), time(8,0), usuarios[8], aeronaves[5]),
            (hoje + timedelta(2), time(9,0), time(10,0), usuarios[9], aeronaves[6]),
            (hoje + timedelta(2), time(13,0), time(14,0), usuarios[3], aeronaves[0]),
            (hoje + timedelta(3), time(8,30), time(9,30), usuarios[4], aeronaves[1]),
            (hoje + timedelta(3), time(15,0), time(16,0), usuarios[5], aeronaves[2]),
            (hoje + timedelta(3), time(16,30), time(17,30), usuarios[6], aeronaves[3]),
        ]

        from sqlalchemy import select, and_
        agendamentos = []
        for dia, h_ini, h_fim, user, aero in agendamentos_config:
            dt_ini = datetime.combine(dia, h_ini)
            dt_fim = datetime.combine(dia, h_fim)
            existing = (await session.execute(
                select(Agendamento).where(and_(
                    Agendamento.hora_inicio == dt_ini,
                    Agendamento.aeronave_id == aero.id,
                    Agendamento.usuario_id == user.id,
                ))
            )).scalar_one_or_none()
            if not existing:
                ag = Agendamento(
                    data=dt_ini, hora_inicio=dt_ini, hora_termino=dt_fim,
                    usuario_id=user.id, aeronave_id=aero.id,
                    status=StatusAgendamento.AGENDADO,
                )
                session.add(ag)
                await session.flush()
                agendamentos.append(ag)
            else:
                agendamentos.append(existing)
        await session.commit()

        # --- CRIAR ALGUNS AGENDAMENTOS CONCLUIDOS PARA RELATORIO ---
        for i in range(min(5, len(agendamentos_config))):
            dia, h_ini, h_fim, user, aero = agendamentos_config[i]
            dt_ini = datetime.combine(dia - timedelta(5), h_ini)
            dt_fim = datetime.combine(dia - timedelta(5), h_fim)
            if dt_fim < datetime.now():
                existing = (await session.execute(
                    select(Agendamento).where(and_(
                        Agendamento.hora_inicio == dt_ini,
                        Agendamento.aeronave_id == aero.id,
                    ))
                )).scalar_one_or_none()
                if not existing:
                    ag = Agendamento(
                        data=dt_ini, hora_inicio=dt_ini, hora_termino=dt_fim,
                        usuario_id=user.id, aeronave_id=aero.id,
                        status=StatusAgendamento.CONCLUIDO,
                    )
                    session.add(ag)
                    await session.flush()
                    # Create financeiro for this agendamento
                    from app.models.financeiro import Financeiro
                    fin = await get_or_none(Financeiro, agendamento_id=ag.id)
                    if not fin:
                        minutos = (dt_fim - dt_ini).total_seconds() / 60
                        fin = Financeiro(
                            agendamento_id=ag.id,
                            tempo_ligado_minutos=minutos,
                            valor_energia=minutos * 1.5,
                            valor_acionamento=minutos * 1.0,
                            valor_total=minutos * 2.5,
                            pago=True,
                        )
                        session.add(fin)

        await session.commit()

        print("=" * 50)
        print("Seed concluído com sucesso!")
        print("=" * 50)
        print()
        print("Aeroclubes:", [ac.nome for ac in (ac1, ac2, ac3)])
        print("Usuários:")
        for u in usuarios:
            nivel = u.nivel_acesso.value
            print(f"  {u.email} / {u.nome_completo} ({nivel})")
        print()
        print("Senhas:")
        print("  admin@aeroclub.com / admin123  (proprietario)")
        print("  adm.central@aeroclub.com / adm123  (administrador)")
        print("  adm.norte@aeroclub.com / adm123  (administrador)")
        print("  demais usuarios / 123456  (solicitantes)")


if __name__ == '__main__':
    asyncio.run(seed())
