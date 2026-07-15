import httpx
import logging
import base64
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class CameraService:
    def __init__(self):
        self.camera_ip = settings.CAMERA_IP
        self.camera_user = settings.CAMERA_USER
        self.camera_password = settings.CAMERA_PASSWORD

    async def verificar_online(self) -> bool:
        if not self.camera_ip:
            return False
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"http://{self.camera_ip}/cgi-bin/status",
                    timeout=5,
                    auth=(self.camera_user, self.camera_password) if self.camera_user else None,
                )
                return response.status_code == 200
        except Exception:
            return False

    async def obter_snapshot(self) -> Optional[bytes]:
        if not self.camera_ip:
            return None
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"http://{self.camera_ip}/cgi-bin/snapshot.cgi",
                    timeout=10,
                    auth=(self.camera_user, self.camera_password) if self.camera_user else None,
                )
                if response.status_code == 200:
                    return response.content
                return None
        except Exception as e:
            logger.error(f"Erro ao obter snapshot: {e}")
            return None

    async def obter_snapshot_base64(self) -> Optional[str]:
        data = await self.obter_snapshot()
        if data:
            return base64.b64encode(data).decode("utf-8")
        return None

    async def verificar_iluminacao(self) -> bool:
        snapshot = await self.obter_snapshot()
        if not snapshot:
            return False
        return True
