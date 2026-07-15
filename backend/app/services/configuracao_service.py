from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.models.configuracao import Configuracao


class ConfiguracaoService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def obter(self, chave: str, padrao: str = None) -> str:
        result = await self.session.execute(select(Configuracao).where(Configuracao.chave == chave))
        config = result.scalar_one_or_none()
        if not config:
            chaves = Configuracao.chaves_padrao()
            if chave in chaves:
                return chaves[chave]["valor"]
            return padrao
        return config.valor

    async def obter_float(self, chave: str, padrao: float = 0) -> float:
        valor = await self.obter(chave, str(padrao))
        try:
            return float(valor)
        except (ValueError, TypeError):
            return padrao

    async def obter_int(self, chave: str, padrao: int = 0) -> int:
        valor = await self.obter(chave, str(padrao))
        try:
            return int(valor)
        except (ValueError, TypeError):
            return padrao

    async def obter_bool(self, chave: str, padrao: bool = False) -> bool:
        valor = await self.obter(chave, str(padrao).lower())
        return valor.lower() in ("true", "1", "yes", "sim")

    async def definir(self, chave: str, valor: str, tipo: str = "texto", descricao: str = None) -> Configuracao:
        result = await self.session.execute(select(Configuracao).where(Configuracao.chave == chave))
        config = result.scalar_one_or_none()
        if config:
            config.valor = valor
            if descricao:
                config.descricao = descricao
        else:
            config = Configuracao(chave=chave, valor=valor, tipo=tipo, descricao=descricao)
            self.session.add(config)
        await self.session.commit()
        await self.session.refresh(config)
        return config

    async def listar_todas(self) -> list[Configuracao]:
        result = await self.session.execute(select(Configuracao).order_by(Configuracao.chave))
        return list(result.scalars().all())

    async def inicializar_padroes(self):
        for chave, config in Configuracao.chaves_padrao().items():
            result = await self.session.execute(select(Configuracao).where(Configuracao.chave == chave))
            if not result.scalar_one_or_none():
                self.session.add(Configuracao(
                    chave=chave,
                    valor=config["valor"],
                    tipo=config["tipo"],
                    descricao=config["descricao"],
                ))
        await self.session.commit()
