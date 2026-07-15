from sqlalchemy import Column, Integer, Float, DateTime, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Financeiro(Base):
    __tablename__ = "financeiro"

    id = Column(Integer, primary_key=True, index=True)
    agendamento_id = Column(Integer, ForeignKey("agendamentos.id"), nullable=False, unique=True)
    tempo_ligado_minutos = Column(Float, nullable=True)
    energia_consumida_kwh = Column(Float, nullable=True)
    valor_energia = Column(Float, nullable=True)
    valor_acionamento = Column(Float, nullable=True)
    impostos = Column(Float, nullable=True, default=0)
    taxas_extras = Column(Float, nullable=True, default=0)
    valor_total = Column(Float, nullable=True)
    pago = Column(Boolean, default=False)
    created_at = Column(DateTime(), server_default=func.now())

    agendamento = relationship("Agendamento", back_populates="financeiro")
