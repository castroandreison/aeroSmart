from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import datetime, date

from app.models.financeiro import Financeiro
from app.models.agendamento import Agendamento, StatusAgendamento
from app.models.usuario import Usuario
from app.models.aeroclube import Aeroclube
from app.services.configuracao_service import ConfiguracaoService


class FinanceiroService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.config_service = ConfiguracaoService(session)

    async def calcular_custos(self, tempo_ligado_minutos: float) -> dict:
        potencia_kw = await self.config_service.obter_float("potencia_instalada_kw", 12)
        valor_kwh = await self.config_service.obter_float("valor_kwh", 0.80)
        valor_acionamento = await self.config_service.obter_float("valor_acionamento", 50)
        tempo_minimo = await self.config_service.obter_int("tempo_minimo_cobranca_min", 30)
        impostos_percent = await self.config_service.obter_float("impostos_percentual", 0)
        taxas_extras = await self.config_service.obter_float("taxas_extras", 0)

        tempo_cobrado = max(tempo_ligado_minutos, tempo_minimo)
        energia_kwh = potencia_kw * (tempo_cobrado / 60)
        valor_energia = energia_kwh * valor_kwh
        impostos_valor = (valor_energia + valor_acionamento) * (impostos_percent / 100)
        valor_total = valor_energia + valor_acionamento + impostos_valor + taxas_extras

        return {
            "tempo_ligado_minutos": tempo_ligado_minutos,
            "energia_consumida_kwh": round(energia_kwh, 2),
            "valor_energia": round(valor_energia, 2),
            "valor_acionamento": round(valor_acionamento, 2),
            "impostos": round(impostos_valor, 2),
            "taxas_extras": round(taxas_extras, 2),
            "valor_total": round(valor_total, 2),
        }

    async def registrar_financeiro(self, agendamento_id: int, tempo_ligado_minutos: float) -> Financeiro:
        custos = await self.calcular_custos(tempo_ligado_minutos)
        financeiro = Financeiro(
            agendamento_id=agendamento_id,
            **custos,
        )
        self.session.add(financeiro)
        await self.session.commit()
        await self.session.refresh(financeiro)
        return financeiro

    async def obter_por_agendamento(self, agendamento_id: int) -> Optional[Financeiro]:
        result = await self.session.execute(select(Financeiro).where(Financeiro.agendamento_id == agendamento_id))
        return result.scalar_one_or_none()

    async def resumo_periodo(self, data_inicio: date, data_fim: date, aeroclube: str = None) -> dict:
        query = select(
            func.count(Financeiro.id),
            func.coalesce(func.sum(Financeiro.valor_total), 0),
            func.coalesce(func.sum(Financeiro.energia_consumida_kwh), 0),
            func.coalesce(func.sum(Financeiro.tempo_ligado_minutos), 0),
        ).join(Agendamento).join(Usuario, Usuario.id == Agendamento.usuario_id).where(
            and_(
                Agendamento.data >= datetime.combine(data_inicio, datetime.min.time()),
                Agendamento.data <= datetime.combine(data_fim, datetime.max.time()),
                Agendamento.status == StatusAgendamento.CONCLUIDO,
            )
        )
        if aeroclube:
            query = query.join(Aeroclube, Aeroclube.id == Usuario.aeroclube_id).where(Aeroclube.nome == aeroclube)
        result = await self.session.execute(query)
        row = result.one()
        return {
            "total_voos": row[0] or 0,
            "total_gasto": float(row[1] or 0),
            "total_energia_kwh": float(row[2] or 0),
            "total_horas": float((row[3] or 0) / 60),
            "periodo_inicio": data_inicio,
            "periodo_fim": data_fim,
        }
