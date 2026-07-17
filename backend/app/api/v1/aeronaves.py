from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional

from app.core.database import get_session
from app.core.security import get_current_user, verificar_admin_ou_proprietario
from app.models.usuario import Usuario, NivelAcesso
from app.models.aeroclube import Aeroclube
from app.schemas.aeronave import AeronaveCreate, AeronaveUpdate, AeronaveResponse
from app.models.aeronave import Aeronave

router = APIRouter(prefix="/aeronaves", tags=["Aeronaves"])


def _build_aero_response(aeronave: Aeronave) -> dict:
    nome = None
    if aeronave.proprietario:
        nome = aeronave.proprietario.nome_completo
    return {
        "id": aeronave.id,
        "matricula": aeronave.matricula,
        "modelo": aeronave.modelo,
        "fabricante": aeronave.fabricante,
        "tipo": aeronave.tipo,
        "peso_maximo": aeronave.peso_maximo,
        "operador": aeronave.operador,
        "usuario_id": aeronave.usuario_id,
        "usuario_nome": nome,
    }


@router.get("/", response_model=List[AeronaveResponse])
async def listar_aeronaves(
    aeroclube_id: Optional[int] = None,
    session: AsyncSession = Depends(get_session),
    current_user: Usuario = Depends(get_current_user),
):
    base_query = select(Aeronave).options(selectinload(Aeronave.proprietario).selectinload(Usuario.aeroclube_rel))
    if current_user.nivel_acesso == NivelAcesso.PROPRIETARIO:
        query = base_query
        if aeroclube_id:
            query = query.join(Usuario, Usuario.id == Aeronave.usuario_id).where(Usuario.aeroclube_id == aeroclube_id)
        result = await session.execute(query.order_by(Aeronave.matricula))
        return [_build_aero_response(a) for a in result.scalars().all()]
    if current_user.nivel_acesso == NivelAcesso.ADMINISTRADOR:
        query = base_query.join(Usuario, Usuario.id == Aeronave.usuario_id)
        if current_user.aeroclube_id:
            query = query.where(Usuario.aeroclube_id == current_user.aeroclube_id)
        result = await session.execute(query.order_by(Aeronave.matricula))
        return [_build_aero_response(a) for a in result.scalars().all()]
    query = base_query.where(Aeronave.usuario_id == current_user.id)
    result = await session.execute(query.order_by(Aeronave.matricula))
    return [_build_aero_response(a) for a in result.scalars().all()]


@router.get("/{aeronave_id}", response_model=AeronaveResponse)
async def obter_aeronave(
    aeronave_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: Usuario = Depends(get_current_user),
):
    result = await session.execute(
        select(Aeronave).options(selectinload(Aeronave.proprietario).selectinload(Usuario.aeroclube_rel)).where(Aeronave.id == aeronave_id)
    )
    aeronave = result.scalar_one_or_none()
    if not aeronave:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aeronave não encontrada")
    if current_user.nivel_acesso == NivelAcesso.PROPRIETARIO:
        return _build_aero_response(aeronave)
    if current_user.nivel_acesso == NivelAcesso.ADMINISTRADOR:
        if aeronave.proprietario and current_user.aeroclube_id and aeronave.proprietario.aeroclube_id != current_user.aeroclube_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")
        return _build_aero_response(aeronave)
    if aeronave.usuario_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")
    return _build_aero_response(aeronave)


@router.post("/", response_model=AeronaveResponse, status_code=status.HTTP_201_CREATED)
async def criar_aeronave(
    data: AeronaveCreate,
    session: AsyncSession = Depends(get_session),
    current_user: Usuario = Depends(get_current_user),
):
    if current_user.nivel_acesso == NivelAcesso.ADMINISTRADOR and current_user.aeroclube_id:
        user_result = await session.execute(select(Usuario).where(Usuario.id == data.usuario_id))
        dono = user_result.scalar_one_or_none()
        if not dono or dono.aeroclube_id != current_user.aeroclube_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Você só pode criar aeronaves para usuários do seu aeroclube")
    aeronave = Aeronave(**data.model_dump(), usuario_id=data.usuario_id or current_user.id)
    session.add(aeronave)
    await session.commit()
    await session.refresh(aeronave)
    return aeronave


@router.put("/{aeronave_id}", response_model=AeronaveResponse)
async def atualizar_aeronave(
    aeronave_id: int,
    data: AeronaveUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: Usuario = Depends(get_current_user),
):
    result = await session.execute(select(Aeronave).where(Aeronave.id == aeronave_id))
    aeronave = result.scalar_one_or_none()
    if not aeronave:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aeronave não encontrada")
    if current_user.nivel_acesso == NivelAcesso.PROPRIETARIO:
        pass
    elif current_user.nivel_acesso == NivelAcesso.ADMINISTRADOR:
        user_result = await session.execute(select(Usuario).where(Usuario.id == aeronave.usuario_id))
        dono = user_result.scalar_one_or_none()
        if not dono or (current_user.aeroclube_id and dono.aeroclube_id != current_user.aeroclube_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")
    elif aeronave.usuario_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(aeronave, key, value)
    await session.commit()
    await session.refresh(aeronave)
    return aeronave


@router.delete("/{aeronave_id}", status_code=status.HTTP_204_NO_CONTENT)
async def excluir_aeronave(
    aeronave_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: Usuario = Depends(get_current_user),
):
    result = await session.execute(select(Aeronave).where(Aeronave.id == aeronave_id))
    aeronave = result.scalar_one_or_none()
    if not aeronave:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aeronave não encontrada")
    if current_user.nivel_acesso == NivelAcesso.PROPRIETARIO:
        pass
    elif current_user.nivel_acesso == NivelAcesso.ADMINISTRADOR:
        user_result = await session.execute(select(Usuario).where(Usuario.id == aeronave.usuario_id))
        dono = user_result.scalar_one_or_none()
        if not dono or (current_user.aeroclube_id and dono.aeroclube_id != current_user.aeroclube_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")
    elif aeronave.usuario_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")
    await session.delete(aeronave)
    await session.commit()
