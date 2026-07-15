from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from sqlalchemy.sql import func

from app.core.database import Base


class Log(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, nullable=True)
    usuario_nome = Column(String(255), nullable=True)
    acao = Column(String(100), nullable=False, index=True)
    entidade = Column(String(100), nullable=True)
    entidade_id = Column(Integer, nullable=True)
    descricao = Column(Text, nullable=True)
    detalhes = Column(JSON, nullable=True)
    ip = Column(String(50), nullable=True)
    created_at = Column(DateTime(), server_default=func.now(), index=True)
