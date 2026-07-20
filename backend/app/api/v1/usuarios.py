from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.core.database import get_session
from app.core.security import get_current_user, verificar_admin_ou_proprietario
from app.models.usuario import Usuario, NivelAcesso
from app.models.aeroclube import Aeroclube
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate, UsuarioResponse, UsuarioList, AlterarSenha
from app.services.usuario_service import UsuarioService

router = APIRouter(prefix="/usuarios", tags=["Usuários"])


@router.get("/", response_model=List[UsuarioList])
async def listar_usuarios(
    ativo: Optional[bool] = None,
    search: Optional[str] = None,
    aeroclube_id: Optional[int] = None,
    session: AsyncSession = Depends(get_session),
    current_user: Usuario = Depends(verificar_admin_ou_proprietario),
):
    service = UsuarioService(session)
    if current_user.nivel_acesso in (NivelAcesso.PROPRIETARIO, NivelAcesso.ADMINISTRADOR):
        return await service.listar(ativo=ativo, search=search, aeroclube_id=aeroclube_id)
    return await service.listar(ativo=ativo, search=search, aeroclube_id=current_user.aeroclube_id)


@router.get("/aeroclubes/lista")
async def listar_aeroclubes(
    session: AsyncSession = Depends(get_session),
    current_user: Usuario = Depends(verificar_admin_ou_proprietario),
):
    result = await session.execute(select(Aeroclube.nome).order_by(Aeroclube.nome))
    return [row[0] for row in result.all()]


@router.get("/{usuario_id}", response_model=UsuarioResponse)
async def obter_usuario(
    usuario_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: Usuario = Depends(get_current_user),
):
    if current_user.nivel_acesso == NivelAcesso.SOLICITANTE and current_user.id != usuario_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")
    service = UsuarioService(session)
    usuario = await service.obter_por_id(usuario_id)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
    if current_user.nivel_acesso == NivelAcesso.ADMINISTRADOR and current_user.aeroclube_id is not None and current_user.aeroclube_id != usuario.aeroclube_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuário não pertence ao seu aeroclube")
    return usuario


@router.post("/", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
async def criar_usuario(
    data: UsuarioCreate,
    session: AsyncSession = Depends(get_session),
    current_user: Usuario = Depends(verificar_admin_ou_proprietario),
):
    if current_user.nivel_acesso == NivelAcesso.ADMINISTRADOR:
        if data.nivel_acesso != NivelAcesso.SOLICITANTE.value:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrador só pode criar solicitantes")
        if data.aeroclube_id and data.aeroclube_id != current_user.aeroclube_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Você só pode criar usuários no seu aeroclube")
    elif current_user.nivel_acesso == NivelAcesso.PROPRIETARIO:
        if data.nivel_acesso != NivelAcesso.ADMINISTRADOR.value:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Proprietário só pode criar administradores")
    service = UsuarioService(session)
    existing = await service.obter_por_email(data.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email já cadastrado")
    usuario = await service.criar(data)
    await service.registrar_log(
        usuario_id=current_user.id,
        usuario_nome=current_user.nome_completo,
        acao="criar_usuario",
        entidade="usuario",
        entidade_id=usuario.id,
        descricao=f"Criou usuário {usuario.nome_completo}",
        ip=current_user.email,
    )
    return usuario


@router.put("/{usuario_id}", response_model=UsuarioResponse)
async def atualizar_usuario(
    usuario_id: int,
    data: UsuarioUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: Usuario = Depends(get_current_user),
):
    if current_user.nivel_acesso == NivelAcesso.SOLICITANTE and current_user.id != usuario_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso restrito")
    service = UsuarioService(session)
    usuario = await service.obter_por_id(usuario_id)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
    if current_user.nivel_acesso == NivelAcesso.ADMINISTRADOR and current_user.aeroclube_id is not None and current_user.aeroclube_id != usuario.aeroclube_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuário não pertence ao seu aeroclube")
    if data.nivel_acesso is not None:
        if current_user.nivel_acesso == NivelAcesso.ADMINISTRADOR and current_user.id != usuario_id and data.nivel_acesso != NivelAcesso.SOLICITANTE.value and data.nivel_acesso != usuario.nivel_acesso.value:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrador só pode alterar para solicitante")
        if current_user.nivel_acesso == NivelAcesso.PROPRIETARIO and data.nivel_acesso != NivelAcesso.ADMINISTRADOR.value and data.nivel_acesso != usuario.nivel_acesso.value:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Proprietário só pode alterar para administrador")
    usuario = await service.atualizar(usuario_id, data)
    return usuario


@router.put("/{usuario_id}/ativar-inativar", response_model=UsuarioResponse)
async def ativar_inativar_usuario(
    usuario_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: Usuario = Depends(verificar_admin_ou_proprietario),
):
    service = UsuarioService(session)
    usuario = await service.obter_por_id(usuario_id)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
    if current_user.nivel_acesso == NivelAcesso.ADMINISTRADOR and current_user.aeroclube_id is not None and current_user.aeroclube_id != usuario.aeroclube_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuário não pertence ao seu aeroclube")
    usuario = await service.ativar_inativar(usuario_id)
    return usuario


@router.post("/alterar-senha")
async def alterar_senha(
    data: AlterarSenha,
    session: AsyncSession = Depends(get_session),
    current_user: Usuario = Depends(get_current_user),
):
    service = UsuarioService(session)
    success = await service.alterar_senha(current_user.id, data.senha_atual, data.nova_senha)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Senha atual inválida")
    return {"message": "Senha alterada com sucesso"}


@router.delete("/{usuario_id}")
async def excluir_usuario(
    usuario_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: Usuario = Depends(verificar_admin_ou_proprietario),
):
    service = UsuarioService(session)
    usuario = await service.obter_por_id(usuario_id)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
    if current_user.nivel_acesso == NivelAcesso.ADMINISTRADOR and current_user.aeroclube_id is not None and current_user.aeroclube_id != usuario.aeroclube_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuário não pertence ao seu aeroclube")
    success = await service.excluir(usuario_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
    await service.registrar_log(
        usuario_id=current_user.id,
        usuario_nome=current_user.nome_completo,
        acao="excluir_usuario",
        entidade="usuario",
        entidade_id=usuario_id,
        descricao=f"Excluiu usuário #{usuario_id}",
    )
    return {"message": "Usuário excluído com sucesso"}


@router.get("/me/perfil", response_model=UsuarioResponse)
async def obter_meu_perfil(
    current_user: Usuario = Depends(get_current_user),
):
    return current_user
