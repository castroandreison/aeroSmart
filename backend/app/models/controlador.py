from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON
from sqlalchemy.sql import func

from app.core.database import Base


class Controlador(Base):
    __tablename__ = "controladores"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    tipo = Column(String(50), nullable=False)
    endpoint = Column(String(500), nullable=True)
    mqtt_topico = Column(String(500), nullable=True)
    configuracao = Column(JSON, nullable=True)
    ativo = Column(Boolean, default=True)
    ultimo_status = Column(String(50), default="desconhecido")
    ultima_comunicacao = Column(DateTime(), nullable=True)
    created_at = Column(DateTime(), server_default=func.now())
