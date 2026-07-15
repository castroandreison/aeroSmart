from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import datetime, date

from app.models.log import Log


class LogService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def registrar(
        self,
        usuario_id: int,
        usuario_nome: str,
        acao: str,
        entidade: str = None,
        entidade_id: int = None,
        descricao: str = None,
        detalhes: dict = None,
        ip: str = None,
    ):
        log = Log(
            usuario_id=usuario_id,
            usuario_nome=usuario_nome,
            acao=acao,
            entidade=entidade,
            entidade_id=entidade_id,
            descricao=descricao,
            detalhes=detalhes,
            ip=ip,
        )
        self.session.add(log)
        await self.session.commit()

    async def listar(
        self,
        usuario_id: Optional[int] = None,
        acao: Optional[str] = None,
        data_inicio: Optional[date] = None,
        data_fim: Optional[date] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Log]:
        query = select(Log)
        if usuario_id:
            query = query.where(Log.usuario_id == usuario_id)
        if acao:
            query = query.where(Log.acao == acao)
        if data_inicio:
            query = query.where(Log.created_at >= data_inicio)
        if data_fim:
            query = query.where(Log.created_at <= data_fim)
        query = query.order_by(Log.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def listar_por_entidade(self, entidade: str, entidade_id: int) -> List[Log]:
        result = await self.session.execute(
            select(Log)
            .where(and_(Log.entidade == entidade, Log.entidade_id == entidade_id))
            .order_by(Log.created_at.desc())
        )
        return list(result.scalars().all())
