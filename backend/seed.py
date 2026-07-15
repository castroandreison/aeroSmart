import asyncio
import sys
sys.path.insert(0, '.')

from app.core.database import async_session_factory, init_db
from app.core.security import hash_password
from app.models.usuario import Usuario, NivelAcesso
from app.models.aeroclube import Aeroclube
from app.models.aeronave import Aeronave
from app.models.agendamento import Agendamento
from app.models.acionamento import Acionamento
from app.models.configuracao import Configuracao
from app.models.controlador import Controlador
from app.models.financeiro import Financeiro
from app.models.log import Log
from app.services.configuracao_service import ConfiguracaoService


async def seed():
    await init_db()
    async with async_session_factory() as session:
        aeroclube = Aeroclube(nome='AeroClub Central')
        session.add(aeroclube)
        await session.commit()
        await session.refresh(aeroclube)

        admin = Usuario(
            nome_completo='Proprietário',
            cpf='000.000.000-00',
            email='admin@aeroclub.com',
            senha_hash=hash_password('admin123'),
            nivel_acesso=NivelAcesso.PROPRIETARIO,
            aeroclube_id=aeroclube.id,
            matricula='ADM001',
            ativo=True,
        )
        session.add(admin)
        await session.commit()
        print(f'Admin criado: admin@aeroclub.com / senha: admin123')

        config_service = ConfiguracaoService(session)
        await config_service.inicializar_padroes()
        print('Configurações padrão criadas')

asyncio.run(seed())
