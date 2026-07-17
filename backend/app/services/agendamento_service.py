from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import datetime, timedelta, date

from app.core.timezone import agora_sp, SAO_PAULO_TZ
from app.models.agendamento import Agendamento, StatusAgendamento
from app.models.acionamento import Acionamento
from app.models.financeiro import Financeiro
from app.models.aeronave import Aeronave
from app.models.usuario import Usuario
from app.schemas.agendamento import AgendamentoCreate, AgendamentoUpdate
from app.services.configuracao_service import ConfiguracaoService


class AgendamentoService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.config_service = ConfiguracaoService(session)

    async def verificar_conflito(
        self, data: date, hora_inicio: datetime, hora_termino: datetime, aeronave_id: int, agendamento_id: Optional[int] = None
    ) -> bool:
        query = select(Agendamento).where(
            and_(
                Agendamento.data >= datetime.combine(data, datetime.min.time()).replace(tzinfo=SAO_PAULO_TZ),
                Agendamento.data < datetime.combine(data + timedelta(days=1), datetime.min.time()).replace(tzinfo=SAO_PAULO_TZ),
                Agendamento.aeronave_id == aeronave_id,
                Agendamento.status.notin_([StatusAgendamento.CANCELADO]),
                or_(
                    and_(
                        Agendamento.hora_inicio < hora_termino,
                        Agendamento.hora_termino > hora_inicio,
                    ),
                ),
            )
        )
        if agendamento_id:
            query = query.where(Agendamento.id != agendamento_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None

    async def verificar_horario_permitido(self, hora_inicio: datetime, hora_termino: datetime) -> bool:
        inicio_str = await self.config_service.obter("horario_inicio_operacao", "06:00")
        fim_str = await self.config_service.obter("horario_fim_operacao", "22:00")

        inicio_oper = datetime.strptime(inicio_str, "%H:%M").time()
        fim_oper = datetime.strptime(fim_str, "%H:%M").time()

        return inicio_oper <= hora_inicio.time() <= fim_oper and inicio_oper <= hora_termino.time() <= fim_oper

    async def listar(
        self, usuario_id: Optional[int] = None, data_inicio: Optional[date] = None, data_fim: Optional[date] = None, status: Optional[str] = None, aeroclube_id: Optional[int] = None, incluir_finalizados: bool = False
    ) -> List[Agendamento]:
        query = select(Agendamento).options(selectinload(Agendamento.solicitante), selectinload(Agendamento.aeronave))
        if usuario_id:
            query = query.where(Agendamento.usuario_id == usuario_id)
        if data_inicio:
            query = query.where(Agendamento.data >= datetime.combine(data_inicio, datetime.min.time()).replace(tzinfo=SAO_PAULO_TZ))
        if data_fim:
            query = query.where(Agendamento.data <= datetime.combine(data_fim, datetime.max.time()).replace(tzinfo=SAO_PAULO_TZ))
        if status:
            query = query.where(Agendamento.status == StatusAgendamento(status))
        if aeroclube_id:
            query = query.join(Usuario, Usuario.id == Agendamento.usuario_id).where(Usuario.aeroclube_id == aeroclube_id)
        if not incluir_finalizados:
            agora = agora_sp()
            query = query.where(
                or_(
                    Agendamento.hora_termino >= agora,
                    Agendamento.status.in_([StatusAgendamento.CONCLUIDO, StatusAgendamento.AGUARDANDO_ENCERRAMENTO, StatusAgendamento.FALHA, StatusAgendamento.CANCELADO])
                )
            )
        # Ordenar: proximos primeiro (hora_inicio >= agora), depois mais antigos
        query = query.order_by(
            Agendamento.hora_inicio >= agora_sp(),
            Agendamento.hora_inicio
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def obter_por_id(self, agendamento_id: int) -> Optional[Agendamento]:
        result = await self.session.execute(
            select(Agendamento)
            .options(selectinload(Agendamento.solicitante), selectinload(Agendamento.aeronave))
            .where(Agendamento.id == agendamento_id)
        )
        return result.scalar_one_or_none()

    async def criar(self, data: AgendamentoCreate, usuario_id: int) -> Agendamento:
        data_date = datetime.strptime(data.data, "%Y-%m-%d").date()
        hora_inicio = datetime.strptime(f"{data.data} {data.hora_inicio}", "%Y-%m-%d %H:%M").replace(tzinfo=SAO_PAULO_TZ)
        hora_termino = datetime.strptime(f"{data.data} {data.hora_termino}", "%Y-%m-%d %H:%M").replace(tzinfo=SAO_PAULO_TZ)

        if data.aeronave_id <= 0:
            raise ValueError("Selecione uma aeronave válida")
        if data_date < agora_sp().date():
            raise ValueError("Nao e permitido agendar para datas passadas")
        if hora_inicio >= hora_termino:
            raise ValueError("Horário de inicio deve ser anterior ao horário de termino")
        if not await self.verificar_horario_permitido(hora_inicio, hora_termino):
            raise ValueError("Horário fora do periodo de operaçao permitido")
        if await self.verificar_conflito(data_date, hora_inicio, hora_termino, data.aeronave_id):
            raise ValueError("Conflito de horário com outro agendamento")

        agendamento = Agendamento(
            data=hora_inicio,
            hora_inicio=hora_inicio,
            hora_termino=hora_termino,
            aeronave_id=data.aeronave_id,
            usuario_id=usuario_id,
            observacoes=data.observacoes,
            status=StatusAgendamento.AGENDADO,
        )
        self.session.add(agendamento)
        await self.session.commit()
        await self.session.refresh(agendamento)
        # Force load lazy relationships for async safety
        agendamento = (await self.session.execute(
            select(Agendamento)
            .options(selectinload(Agendamento.solicitante).selectinload(Usuario.aeroclube_rel), selectinload(Agendamento.aeronave))
            .where(Agendamento.id == agendamento.id)
        )).scalar_one()
        return agendamento


    async def atualizar(self, agendamento_id: int, data: AgendamentoUpdate, usuario_id: int) -> Optional[Agendamento]:
        agendamento = await self.obter_por_id(agendamento_id)
        if not agendamento:
            return None
        if agendamento.status == StatusAgendamento.CONCLUIDO:
            raise ValueError("Nao e possivel editar um agendamento concluido")
        if agendamento.status == StatusAgendamento.CANCELADO:
            raise ValueError("Nao e possivel editar um agendamento cancelado")

        update_data = data.model_dump(exclude_unset=True)
        if "data" in update_data or "hora_inicio" in update_data or "hora_termino" in update_data:
            new_data = update_data.get("data", agendamento.data.strftime("%Y-%m-%d"))
            new_hora_inicio = update_data.get("hora_inicio", agendamento.hora_inicio.strftime("%H:%M"))
            new_hora_termino = update_data.get("hora_termino", agendamento.hora_termino.strftime("%H:%M"))

            data_date = datetime.strptime(new_data, "%Y-%m-%d").date()
            hora_inicio = datetime.strptime(f"{new_data} {new_hora_inicio}", "%Y-%m-%d %H:%M").replace(tzinfo=SAO_PAULO_TZ)
            hora_termino = datetime.strptime(f"{new_data} {new_hora_termino}", "%Y-%m-%d %H:%M").replace(tzinfo=SAO_PAULO_TZ)

            aeronave_id = update_data.get("aeronave_id", agendamento.aeronave_id)

            if hora_inicio >= hora_termino:
                raise ValueError("Horário de inicio deve ser anterior ao horário de termino")
            if await self.verificar_conflito(data_date, hora_inicio, hora_termino, aeronave_id, agendamento_id):
                raise ValueError("Conflito de horário com outro agendamento")

            agendamento.data = hora_inicio
            agendamento.hora_inicio = hora_inicio
            agendamento.hora_termino = hora_termino

        for key, value in update_data.items():
            if key not in ("data", "hora_inicio", "hora_termino"):
                setattr(agendamento, key, value)

        agendamento.updated_at = agora_sp()
        await self.session.commit()
        agendamento = (await self.session.execute(
            select(Agendamento)
            .options(selectinload(Agendamento.solicitante), selectinload(Agendamento.aeronave))
            .where(Agendamento.id == agendamento.id)
        )).scalar_one()
        return agendamento

    async def finalizar_agendamentos_passados(self) -> int:
        agora = agora_sp()
        query = select(Agendamento).where(
            Agendamento.hora_termino < agora,
            Agendamento.status.notin_([StatusAgendamento.CONCLUIDO, StatusAgendamento.CANCELADO]),
        )
        result = await self.session.execute(query)
        agendamentos = list(result.scalars().all())
        for ag in agendamentos:
            ag.status = StatusAgendamento.CONCLUIDO
        if agendamentos:
            await self.session.commit()
        return len(agendamentos)

    async def cancelar(self, agendamento_id: int) -> bool:
        agendamento = await self.obter_por_id(agendamento_id)
        if not agendamento:
            return False
        if agendamento.status == StatusAgendamento.CONCLUIDO:
            raise ValueError("Nao e possivel cancelar um agendamento concluido")
        if agendamento.status == StatusAgendamento.CANCELADO:
            return False
        agendamento.status = StatusAgendamento.CANCELADO
        await self.session.commit()
        return True

    async def excluir(self, agendamento_id: int) -> bool:
        agendamento = await self.obter_por_id(agendamento_id)
        if not agendamento:
            return False
        # Remove registros associados antes de excluir o agendamento
        result = await self.session.execute(
            select(Acionamento).where(Acionamento.agendamento_id == agendamento_id)
        )
        acionamento = result.scalar_one_or_none()
        if acionamento:
            await self.session.delete(acionamento)
        try:
            result = await self.session.execute(
                select(Financeiro).where(Financeiro.agendamento_id == agendamento_id)
            )
            financeiro = result.scalar_one_or_none()
            if financeiro:
                await self.session.delete(financeiro)
        except Exception:
            pass
        await self.session.delete(agendamento)
        await self.session.commit()
        return True

    async def confirmar_agendamento(self, agendamento_id: int) -> Optional[Agendamento]:
        agendamento = await self.obter_por_id(agendamento_id)
        if not agendamento:
            return None
        if agendamento.status == StatusAgendamento.AGENDADO:
            agendamento.status = StatusAgendamento.CONFIRMADO
            await self.session.commit()
            await self.session.refresh(agendamento)
        return agendamento


    async def finalizar_agendamento(self, agendamento_id: int) -> Optional[Agendamento]:
        agendamento = await self.obter_por_id(agendamento_id)
        if not agendamento:
            return None
        if agendamento.status in (StatusAgendamento.CONFIRMADO, StatusAgendamento.AGENDADO):
            agendamento.status = StatusAgendamento.CONCLUIDO
            await self.session.commit()
            await self.session.refresh(agendamento)
        return agendamento


