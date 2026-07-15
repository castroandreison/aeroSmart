from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from app.core.database import Base


class Alerta(Base):
    __tablename__ = "alertas"

    id = Column(Integer, primary_key=True, index=True)
    estacao = Column(String(255), nullable=False)
    comando = Column(String(50), nullable=False)
    mensagem = Column(Text, nullable=True)
    lido = Column(Boolean, default=False)
    created_at = Column(DateTime(), server_default=func.now())
