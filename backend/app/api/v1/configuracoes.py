from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_session
from app.core.security import get_current_user, verificar_admin_ou_proprietario
from app.models.usuario import Usuario
from app.services.configuracao_service import ConfiguracaoService

router = APIRouter(prefix="/configuracoes", tags=["Configurações"])


class ConfiguracaoUpdate(BaseModel):
    valor: str
    descricao: Optional[str] = None


class ConfiguracaoResponse(BaseModel):
    chave: str
    valor: str
    tipo: str
    descricao: Optional[str] = None

    class Config:
        from_attributes = True


@router.get("/", response_model=List[ConfiguracaoResponse])
async def listar_configuracoes(
    session: AsyncSession = Depends(get_session),
    current_user: Usuario = Depends(verificar_admin_ou_proprietario),
):
    service = ConfiguracaoService(session)
    configs = await service.listar_todas(aeroclube_id=current_user.aeroclube_id)
    if not configs and current_user.aeroclube_id:
        await service.inicializar_padroes(aeroclube_id=current_user.aeroclube_id)
        configs = await service.listar_todas(aeroclube_id=current_user.aeroclube_id)
    return configs


@router.put("/{chave}", response_model=ConfiguracaoResponse)
async def atualizar_configuracao(
    chave: str,
    data: ConfiguracaoUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: Usuario = Depends(verificar_admin_ou_proprietario),
):
    service = ConfiguracaoService(session)
    config = await service.definir(chave, data.valor, descricao=data.descricao, aeroclube_id=current_user.aeroclube_id)
    return config


@router.post("/inicializar")
async def inicializar_configuracoes(
    session: AsyncSession = Depends(get_session),
    current_user: Usuario = Depends(verificar_admin_ou_proprietario),
):
    service = ConfiguracaoService(session)
    await service.inicializar_padroes(aeroclube_id=current_user.aeroclube_id)
    return {"message": "Configurações iniciais criadas com sucesso"}
