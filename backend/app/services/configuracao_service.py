from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.models.configuracao import Configuracao


class ConfiguracaoService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def obter(self, chave: str, padrao: str = None, aeroclube_id: int = None) -> str:
        config = await self._buscar(chave, aeroclube_id)
        if not config:
            config = await self._buscar(chave, None)
        if not config:
            chaves = Configuracao.chaves_padrao()
            if chave in chaves:
                return chaves[chave]["valor"]
            return padrao
        return config.valor

    async def _buscar(self, chave: str, aeroclube_id: int = None) -> Optional[Configuracao]:
        result = await self.session.execute(
            select(Configuracao).where(
                Configuracao.chave == chave,
                Configuracao.aeroclube_id == aeroclube_id,
            )
        )
        return result.scalar_one_or_none()

    async def obter_float(self, chave: str, padrao: float = 0, aeroclube_id: int = None) -> float:
        valor = await self.obter(chave, str(padrao), aeroclube_id=aeroclube_id)
        try:
            return float(valor)
        except (ValueError, TypeError):
            return padrao

    async def obter_int(self, chave: str, padrao: int = 0, aeroclube_id: int = None) -> int:
        valor = await self.obter(chave, str(padrao), aeroclube_id=aeroclube_id)
        try:
            return int(valor)
        except (ValueError, TypeError):
            return padrao

    async def obter_bool(self, chave: str, padrao: bool = False, aeroclube_id: int = None) -> bool:
        valor = await self.obter(chave, str(padrao).lower(), aeroclube_id=aeroclube_id)
        return valor.lower() in ("true", "1", "yes", "sim")

    async def definir(self, chave: str, valor: str, tipo: str = "texto", descricao: str = None, aeroclube_id: int = None) -> Configuracao:
        config = await self._buscar(chave, aeroclube_id)
        if config:
            config.valor = valor
            if descricao:
                config.descricao = descricao
        else:
            config = Configuracao(chave=chave, valor=valor, tipo=tipo, descricao=descricao, aeroclube_id=aeroclube_id)
            self.session.add(config)
        await self.session.commit()
        await self.session.refresh(config)
        return config

    async def listar_todas(self, aeroclube_id: int = None) -> list[Configuracao]:
        result = await self.session.execute(
            select(Configuracao)
            .where(Configuracao.aeroclube_id == aeroclube_id)
            .order_by(Configuracao.chave)
        )
        return list(result.scalars().all())

    async def inicializar_padroes(self, aeroclube_id: int = None):
        for chave, config in Configuracao.chaves_padrao().items():
            existing = await self._buscar(chave, aeroclube_id)
            if not existing:
                self.session.add(Configuracao(
                    chave=chave,
                    valor=config["valor"],
                    tipo=config["tipo"],
                    descricao=config["descricao"],
                    aeroclube_id=aeroclube_id,
                ))
        await self.session.commit()
