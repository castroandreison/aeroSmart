from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import create_access_token, verify_password
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.usuario_service import UsuarioService
from app.models.usuario import NivelAcesso

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, session: AsyncSession = Depends(get_session)):
    service = UsuarioService(session)
    usuario = await service.obter_por_email(data.email)
    if not usuario or not verify_password(data.senha, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha inválidos",
        )
    if not usuario.ativo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário inativo",
        )

    access_token = create_access_token(data={"sub": usuario.id})
    await service.registrar_login(usuario.id)
    await service.registrar_log(
        usuario_id=usuario.id,
        usuario_nome=usuario.nome_completo,
        acao="login",
        descricao="Usuário realizou login",
    )

    return TokenResponse(
        access_token=access_token,
        usuario_id=usuario.id,
        nome=usuario.nome_completo,
        email=usuario.email,
        nivel_acesso=usuario.nivel_acesso.value,
    )
