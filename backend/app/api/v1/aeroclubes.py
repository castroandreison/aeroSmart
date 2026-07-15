from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_session
from app.core.security import verificar_admin_ou_proprietario
from app.models.usuario import Usuario
from app.schemas.aeroclube import AeroclubeCreate, AeroclubeUpdate, AeroclubeResponse
from app.services.aeroclube_service import AeroclubeService

router = APIRouter(prefix="/aeroclubes", tags=["Aeroclubes"])


@router.get("/", response_model=List[AeroclubeResponse])
async def listar_aeroclubes(
    session: AsyncSession = Depends(get_session),
    current_user: Usuario = Depends(verificar_admin_ou_proprietario),
):
    service = AeroclubeService(session)
    return await service.listar()


@router.get("/{aeroclube_id}", response_model=AeroclubeResponse)
async def obter_aeroclube(
    aeroclube_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: Usuario = Depends(verificar_admin_ou_proprietario),
):
    service = AeroclubeService(session)
    aeroclube = await service.obter_por_id(aeroclube_id)
    if not aeroclube:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aeroclube não encontrado")
    return aeroclube


@router.post("/", response_model=AeroclubeResponse, status_code=status.HTTP_201_CREATED)
async def criar_aeroclube(
    data: AeroclubeCreate,
    session: AsyncSession = Depends(get_session),
    current_user: Usuario = Depends(verificar_admin_ou_proprietario),
):
    service = AeroclubeService(session)
    try:
        aeroclube = await service.criar(data)
        return aeroclube
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{aeroclube_id}", response_model=AeroclubeResponse)
async def atualizar_aeroclube(
    aeroclube_id: int,
    data: AeroclubeUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: Usuario = Depends(verificar_admin_ou_proprietario),
):
    service = AeroclubeService(session)
    aeroclube = await service.atualizar(aeroclube_id, data)
    if not aeroclube:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aeroclube não encontrado")
    return aeroclube


@router.delete("/{aeroclube_id}")
async def excluir_aeroclube(
    aeroclube_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: Usuario = Depends(verificar_admin_ou_proprietario),
):
    service = AeroclubeService(session)
    success = await service.excluir(aeroclube_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aeroclube não encontrado")
    return {"message": "Aeroclube excluído com sucesso"}
