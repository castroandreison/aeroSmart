from sqlalchemy import Column, Integer, DateTime, String, Text, ForeignKey, Float, Enum as SAEnum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class StatusAgendamento(str, enum.Enum):
    AGENDADO = "agendado"
    CONFIRMADO = "confirmado"
    EM_ANDAMENTO = "em_andamento"
    AGUARDANDO_ENCERRAMENTO = "aguardando_encerramento"
    CONCLUIDO = "concluido"
    CANCELADO = "cancelado"
    FALHA = "falha"


class Agendamento(Base):
    __tablename__ = "agendamentos"

    id = Column(Integer, primary_key=True, index=True)
    data = Column(DateTime(), nullable=False, index=True)
    hora_inicio = Column(DateTime(), nullable=False)
    hora_termino = Column(DateTime(), nullable=False)
    observacoes = Column(Text, nullable=True)
    status = Column(SAEnum(StatusAgendamento), default=StatusAgendamento.AGENDADO)

    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    aeronave_id = Column(Integer, ForeignKey("aeronaves.id"), nullable=False)
    aeroclube_id = Column(Integer, ForeignKey("aeroclubes.id"), nullable=True)

    created_at = Column(DateTime(), server_default=func.now())
    updated_at = Column(DateTime(), onupdate=func.now())
    created_by = Column(Integer, nullable=True)

    solicitante = relationship("Usuario", back_populates="agendamentos")
    aeronave = relationship("Aeronave", back_populates="agendamentos")
    aeroclube_rel = relationship("Aeroclube", back_populates="agendamentos")
    acionamento = relationship("Acionamento", back_populates="agendamento", uselist=False)
    financeiro = relationship("Financeiro", back_populates="agendamento", uselist=False)
