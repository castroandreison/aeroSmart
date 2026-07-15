import httpx
import logging
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class WhatsAppService:
    def __init__(self):
        self.api_url = settings.WHATSAPP_API_URL
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
        self.token = settings.WHATSAPP_TOKEN

    async def enviar_mensagem(self, para: str, mensagem: str) -> bool:
        if not self.phone_number_id or not self.token:
            logger.warning("WhatsApp não configurado")
            return False

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/{self.phone_number_id}/messages",
                    headers={
                        "Authorization": f"Bearer {self.token}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "messaging_product": "whatsapp",
                        "to": para,
                        "type": "text",
                        "text": {"body": mensagem},
                    },
                    timeout=30,
                )
                response.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"Erro ao enviar WhatsApp: {e}")
            return False

    async def notificar_ligamento(self, nome: str, whatsapp: str, hora: str) -> bool:
        mensagem = (
            f"Olá, {nome}\n\n"
            f"Seu agendamento foi iniciado.\n"
            f"A pista encontra-se com o balizamento LIGADO.\n\n"
            f"Horário:\n"
            f"{hora}\n\n"
            f"Bom voo."
        )
        return await self.enviar_mensagem(whatsapp, mensagem)

    async def notificar_desligamento(self, nome: str, whatsapp: str) -> bool:
        mensagem = (
            f"Olá, {nome}\n\n"
            f"Seu período de utilização foi encerrado.\n"
            f"O balizamento foi DESLIGADO.\n\n"
            f"Obrigado."
        )
        return await self.enviar_mensagem(whatsapp, mensagem)
