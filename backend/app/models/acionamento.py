from sqlalchemy import Column, Integer, DateTime, Float, ForeignKey, String, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Acionamento(Base):
    __tablename__ = "acionamentos"

    id = Column(Integer, primary_key=True, index=True)
    agendamento_id = Column(Integer, ForeignKey("agendamentos.id"), nullable=False, unique=True)
    data_hora_ligamento = Column(DateTime(), nullable=False)
    data_hora_desligamento = Column(DateTime(), nullable=True)
    tempo_ligado_segundos = Column(Float, nullable=True)
    status = Column(String(50), default="pendente")
    confirmado = Column(Boolean, default=False)
    whatsapp_enviado_ligar = Column(Boolean, default=False)
    whatsapp_enviado_desligar = Column(Boolean, default=False)
    created_at = Column(DateTime(), server_default=func.now())

    agendamento = relationship("Agendamento", back_populates="acionamento")
