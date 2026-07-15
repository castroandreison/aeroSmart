from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import date

from app.core.database import get_session
from app.core.security import get_current_user, verificar_admin_ou_proprietario
from app.models.usuario import Usuario
from app.schemas.log import LogResponse
from app.services.log_service import LogService

router = APIRouter(prefix="/logs", tags=["Logs"])


@router.get("/", response_model=List[LogResponse])
async def listar_logs(
    usuario_id: Optional[int] = None,
    acao: Optional[str] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
    admin: Usuario = Depends(verificar_admin_ou_proprietario),
):
    service = LogService(session)
    dt_inicio = date.fromisoformat(data_inicio) if data_inicio else None
    dt_fim = date.fromisoformat(data_fim) if data_fim else None
    return await service.listar(
        usuario_id=usuario_id,
        acao=acao,
        data_inicio=dt_inicio,
        data_fim=dt_fim,
        limit=limit,
        offset=offset,
    )
