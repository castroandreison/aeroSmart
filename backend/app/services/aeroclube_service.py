from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from app.models.aeroclube import Aeroclube
from app.schemas.aeroclube import AeroclubeCreate, AeroclubeUpdate
from app.services.configuracao_service import ConfiguracaoService


class AeroclubeService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def listar(self) -> List[Aeroclube]:
        result = await self.session.execute(select(Aeroclube).order_by(Aeroclube.nome))
        return list(result.scalars().all())

    async def obter_por_id(self, aeroclube_id: int) -> Optional[Aeroclube]:
        result = await self.session.execute(select(Aeroclube).where(Aeroclube.id == aeroclube_id))
        return result.scalar_one_or_none()

    async def obter_por_nome(self, nome: str) -> Optional[Aeroclube]:
        result = await self.session.execute(select(Aeroclube).where(Aeroclube.nome == nome))
        return result.scalar_one_or_none()

    async def _gerar_topicos(self, nome: str) -> tuple[str, str]:
        svc = ConfiguracaoService(self.session)
        prefixo = await svc.obter("mqtt_topic_prefix", "Bal")
        return f"{prefixo}/Write/{nome}", f"{prefixo}/Read/{nome}"

    async def criar(self, data: AeroclubeCreate) -> Aeroclube:
        existing = await self.obter_por_nome(data.nome)
        if existing:
            raise ValueError("Aeroclube já existe")
        topic_write, topic_read = await self._gerar_topicos(data.nome)
        aeroclube = Aeroclube(nome=data.nome, topic_write=topic_write, topic_read=topic_read)
        self.session.add(aeroclube)
        await self.session.commit()
        await self.session.refresh(aeroclube)
        return aeroclube

    async def atualizar(self, aeroclube_id: int, data: AeroclubeUpdate) -> Optional[Aeroclube]:
        aeroclube = await self.obter_por_id(aeroclube_id)
        if not aeroclube:
            return None
        update_data = data.model_dump(exclude_unset=True)
        if "nome" in update_data and update_data["nome"] != aeroclube.nome:
            topic_write, topic_read = await self._gerar_topicos(update_data["nome"])
            update_data["topic_write"] = topic_write
            update_data["topic_read"] = topic_read
        for key, value in update_data.items():
            setattr(aeroclube, key, value)
        await self.session.commit()
        await self.session.refresh(aeroclube)
        return aeroclube

    async def excluir(self, aeroclube_id: int) -> bool:
        aeroclube = await self.obter_por_id(aeroclube_id)
        if not aeroclube:
            return False
        await self.session.delete(aeroclube)
        await self.session.commit()
        return True
