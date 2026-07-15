from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from app.models.usuario import Usuario, NivelAcesso
from app.models.log import Log
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate
from app.core.security import hash_password, verify_password
from datetime import datetime


class UsuarioService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def listar(self, ativo: Optional[bool] = None, search: Optional[str] = None,
                     aeroclube_id: Optional[int] = None) -> List[Usuario]:
        query = select(Usuario)
        if ativo is not None:
            query = query.where(Usuario.ativo == ativo)
        if aeroclube_id is not None:
            query = query.where(Usuario.aeroclube_id == aeroclube_id)
        if search:
            query = query.where(
                or_(
                    Usuario.nome_completo.ilike(f"%{search}%"),
                    Usuario.email.ilike(f"%{search}%"),
                    Usuario.matricula.ilike(f"%{search}%"),
                    Usuario.cpf.ilike(f"%{search}%"),
                )
            )
        query = query.order_by(Usuario.nome_completo)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def obter_por_id(self, usuario_id: int) -> Optional[Usuario]:
        result = await self.session.execute(select(Usuario).where(Usuario.id == usuario_id))
        return result.scalar_one_or_none()

    async def obter_por_email(self, email: str) -> Optional[Usuario]:
        result = await self.session.execute(select(Usuario).where(Usuario.email == email))
        return result.scalar_one_or_none()

    async def criar(self, data: UsuarioCreate) -> Usuario:
        usuario = Usuario(
            nome_completo=data.nome_completo,
            cpf=data.cpf,
            crea=data.crea,
            empresa_operador=data.empresa_operador,
            aeroclube_id=data.aeroclube_id,
            telefone=data.telefone,
            whatsapp=data.whatsapp,
            email=data.email,
            senha_hash=hash_password(data.senha),
            matricula=data.matricula,
            codigo_interno=data.codigo_interno,
            observacoes=data.observacoes,
            nivel_acesso=NivelAcesso(data.nivel_acesso) if data.nivel_acesso else NivelAcesso.SOLICITANTE,
        )
        self.session.add(usuario)
        await self.session.commit()
        await self.session.refresh(usuario)
        return usuario

    async def atualizar(self, usuario_id: int, data: UsuarioUpdate) -> Optional[Usuario]:
        usuario = await self.obter_por_id(usuario_id)
        if not usuario:
            return None
        update_data = data.model_dump(exclude_unset=True)
        if "nivel_acesso" in update_data:
            update_data["nivel_acesso"] = NivelAcesso(update_data["nivel_acesso"])
        for key, value in update_data.items():
            setattr(usuario, key, value)
        await self.session.commit()
        await self.session.refresh(usuario)
        return usuario

    async def alterar_senha(self, usuario_id: int, senha_atual: str, nova_senha: str) -> bool:
        usuario = await self.obter_por_id(usuario_id)
        if not usuario or not verify_password(senha_atual, usuario.senha_hash):
            return False
        usuario.senha_hash = hash_password(nova_senha)
        await self.session.commit()
        return True

    async def ativar_inativar(self, usuario_id: int) -> Optional[Usuario]:
        usuario = await self.obter_por_id(usuario_id)
        if not usuario:
            return None
        usuario.ativo = not usuario.ativo
        await self.session.commit()
        await self.session.refresh(usuario)
        return usuario

    async def excluir(self, usuario_id: int) -> bool:
        usuario = await self.obter_por_id(usuario_id)
        if not usuario:
            return False
        await self.session.delete(usuario)
        await self.session.commit()
        return True

    async def registrar_login(self, usuario_id: int):
        usuario = await self.obter_por_id(usuario_id)
        if usuario:
            usuario.ultimo_login = datetime.utcnow()
            await self.session.commit()

    async def registrar_log(self, usuario_id: int, usuario_nome: str, acao: str, entidade: str = None, entidade_id: int = None, descricao: str = None, detalhes: dict = None, ip: str = None):
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
